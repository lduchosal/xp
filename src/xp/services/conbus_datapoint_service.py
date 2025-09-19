"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import socket
import logging
import yaml
import os
from typing import List, Optional
from datetime import datetime

from ..models import (
    ConbusClientConfig,
    ConbusDatapointRequest,
    ConbusDatapointResponse,
    DatapointTypeName,
    ConbusConnectionStatus,
)
from ..models.datapoint_type import DataPointType
from ..models.response import Response
from ..services.telegram_service import TelegramService
from ..services.telegram_version_service import VersionService
from ..utils.checksum import calculate_checksum


class ConbusDatapointError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusDatapointService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus client send service"""
        self.config_path = config_path
        self.config = ConbusClientConfig()
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.last_activity: Optional[datetime] = None

        # Service dependencies
        self.telegram_service = TelegramService()
        self.version_service = VersionService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load client configuration from cli.yml"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as file:
                    config_data = yaml.safe_load(file)
                    conbus_config = config_data.get("conbus", {})

                    self.config.ip = conbus_config.get("ip", self.config.ip)
                    self.config.port = conbus_config.get("port", self.config.port)
                    self.config.timeout = conbus_config.get(
                        "timeout", self.config.timeout
                    )

                    self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.logger.warning(
                    f"Config file {self.config_path} not found, using defaults"
                )
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")

    def get_config(self) -> ConbusClientConfig:
        """Get current client configuration"""
        return self.config

    def connect(self) -> Response:
        """Establish TCP connection to the Conbus server"""
        if self.is_connected:
            return Response(
                success=True,
                data={"message": "Already connected", "config": self.config.to_dict()},
                error=None,
            )

        try:
            # Create TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.timeout)

            # Connect to server
            self.socket.connect((self.config.ip, self.config.port))
            self.is_connected = True
            self.last_activity = datetime.now()

            self.logger.info(
                f"Connected to Conbus server at {self.config.ip}:{self.config.port}"
            )

            return Response(
                success=True,
                data={
                    "message": f"Connected to {self.config.ip}:{self.config.port}",
                    "config": self.config.to_dict(),
                },
                error=None,
            )

        except socket.timeout:
            error_msg = f"Connection timeout after {self.config.timeout} seconds"
            self.logger.error(error_msg)
            return Response(success=False, data=None, error=error_msg)
        except Exception as e:
            error_msg = f"Failed to connect to {self.config.ip}:{self.config.port}: {e}"
            self.logger.error(error_msg)
            return Response(success=False, data=None, error=error_msg)

    def disconnect(self):
        """Close TCP connection to the server"""
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("Disconnected from Conbus server")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
            finally:
                self.socket = None
                self.is_connected = False

    def get_connection_status(self) -> ConbusConnectionStatus:
        """Get current connection status"""
        return ConbusConnectionStatus(
            connected=self.is_connected,
            ip=self.config.ip,
            port=self.config.port,
            last_activity=self.last_activity,
        )

    def send_telegram(self, request: ConbusDatapointRequest) -> ConbusDatapointResponse:
        """Send a telegram to the Conbus server"""
        if not self.is_connected:
            # Try to connect automatically
            connect_result = self.connect()
            if not connect_result.success:
                return ConbusDatapointResponse(
                    success=False,
                    request=request,
                    error=f"Not connected to server: {connect_result.error}",
                )

        try:
            # Generate telegram based on type
            telegram = self._generate_telegram(request)
            if not telegram:
                return ConbusDatapointResponse(
                    success=False,
                    request=request,
                    error=f"Failed to generate telegram for type {request.datapoint_type.value}",
                )

            # Send telegram
            self.socket.send(telegram.encode("latin-1"))
            self.last_activity = datetime.now()

            self.logger.info(f"Sent telegram: {telegram}")

            # Receive responses (with timeout)
            responses = self._receive_responses()

            return ConbusDatapointResponse(
                success=True,
                request=request,
                sent_telegram=telegram,
                received_telegrams=responses,
            )

        except socket.timeout:
            error_msg = "Response timeout"
            self.logger.error(error_msg)
            return ConbusDatapointResponse(success=False, request=request, error=error_msg)
        except Exception as e:
            error_msg = f"Failed to send telegram: {e}"
            self.logger.error(error_msg)
            return ConbusDatapointResponse(success=False, request=request, error=error_msg)

    def _generate_telegram(self, request: ConbusDatapointRequest) -> Optional[str]:
        """Generate telegram string based on request type"""
        try:
            if not request.target_serial:
                return None

            if request.datapoint_type in [
                DatapointTypeName.VERSION,
                DatapointTypeName.VOLTAGE,
                DatapointTypeName.TEMPERATURE,
                DatapointTypeName.CURRENT,
                DatapointTypeName.HUMIDITY,
            ]:
                return self._generate_sensor_telegram(request)

            else:
                return None

        except Exception as e:
            self.logger.error(f"Error generating telegram: {e}")
            return None

    def _generate_sensor_telegram(self, request: ConbusDatapointRequest) -> Optional[str]:
        """Generate sensor data request telegram"""
        if not request.target_serial:
            return None

        # Map telegram types to data point codes
        sensor_data_points = {
            DatapointTypeName.VERSION: DataPointType.VERSION.value,  # Version data point
            DatapointTypeName.VOLTAGE: DataPointType.VOLTAGE.value,  # Voltage data point
            DatapointTypeName.TEMPERATURE: DataPointType.TEMPERATURE.value,  # Temperature data point
            DatapointTypeName.CURRENT: DataPointType.CURRENT.value,  # Current data point
            DatapointTypeName.HUMIDITY: DataPointType.HUMIDITY.value,  # Humidity data point
        }

        data_point = sensor_data_points.get(request.datapoint_type)
        if not data_point:
            return None

        # Generate system telegram: <S{serial}F02D{data_point}{checksum}>
        telegram_body = f"S{request.target_serial}F02D{data_point}"
        checksum = calculate_checksum(telegram_body)
        telegram = f"<{telegram_body}{checksum}>"

        return telegram

    def _receive_responses(self) -> List[str]:
        """Receive responses from the server"""
        responses = []

        try:
            # Set a shorter timeout for receiving responses
            original_timeout = self.socket.gettimeout()
            self.socket.settimeout(2.0)  # 2 second timeout for responses

            while True:
                try:
                    data = self.socket.recv(1024)
                    if not data:
                        break

                    message = data.decode("latin-1").strip()
                    if message:
                        responses.append(message)
                        self.logger.info(f"Received: {message}")
                        self.last_activity = datetime.now()

                except socket.timeout:
                    # No more data available
                    break

            # Restore original timeout
            self.socket.settimeout(original_timeout)

        except Exception as e:
            self.logger.error(f"Error receiving responses: {e}")

        return responses

    def send_version_request(self, target_serial: str) -> ConbusDatapointResponse:
        """Send version request telegram"""
        request = ConbusDatapointRequest(
            datapoint_type=DatapointTypeName.VERSION, target_serial=target_serial
        )
        return self.send_telegram(request)

    def datapoint_request(
        self, target_serial: str, sensor_type: DatapointTypeName
    ) -> ConbusDatapointResponse:
        print(f"sensor_type.__class__.__module__: {sensor_type.__class__.__module__}")
        print(f"DatapointTypeName.__module__: {DatapointTypeName.__module__}")

        """Send sensor data request telegram"""
        if sensor_type.value not in [
            DatapointTypeName.VOLTAGE.value,
            DatapointTypeName.TEMPERATURE.value,
            DatapointTypeName.CURRENT.value,
            DatapointTypeName.HUMIDITY.value,
        ]:
            raise ConbusDatapointError(f"Invalid sensor type: {sensor_type.value}")

        request = ConbusDatapointRequest(
            datapoint_type=sensor_type, target_serial=target_serial
        )
        return self.send_telegram(request)

    def scan_module(
        self, target_serial: str, function_code: str, progress_callback=None
    ) -> List[ConbusDatapointResponse]:
        """Scan all functions and datapoints for a module with live output"""
        results = []
        total_combinations = 256 * 256  # 65536 combinations
        count = 0

        for datapoint_hex in range(256):
            datapoint_code = f"{datapoint_hex:02X}"
            count += 1

            try:
                response = self.send_custom_telegram(
                    target_serial, function_code, datapoint_code
                )
                results.append(response)

                # Call progress callback with live results
                if progress_callback:
                    progress_callback(response, count, total_combinations)

                # Small delay to prevent overwhelming the server
                import time

                time.sleep(0.001)  # 1ms delay

            except Exception as e:
                # Create error response for failed scan attempt
                error_response = ConbusDatapointResponse(
                    success=False,
                    request=ConbusDatapointRequest(
                        datapoint_type=DatapointTypeName.UNKNOWN,  # Placeholder
                        target_serial=target_serial,
                        function_code=function_code,
                        datapoint_code=datapoint_code,
                    ),
                    error=f"Scan failed for F{function_code}D{datapoint_code}: {e}",
                )
                results.append(error_response)

                # Call progress callback with error response
                if progress_callback:
                    progress_callback(error_response, count, total_combinations)

        return results

    def scan_module_background(self, target_serial: str, progress_callback=None):
        """Scan module in background with immediate output via callback"""
        import threading

        def background_scan():
            return self.scan_module(target_serial, progress_callback)

        # Start background thread
        scan_thread = threading.Thread(target=background_scan, daemon=True)
        scan_thread.start()

        return scan_thread

    def send_custom_telegram(
        self, target_serial: str, function_code: str, datapoint_code: str
    ) -> ConbusDatapointResponse:
        """Send custom telegram with specified function and data point codes"""
        # Generate custom system telegram: <S{serial}F{function}{data_point}{checksum}>
        telegram_body = f"S{target_serial}F{function_code}D{datapoint_code}"
        checksum = calculate_checksum(telegram_body)
        telegram = f"<{telegram_body}{checksum}>"

        try:
            if not self.is_connected:
                connect_result = self.connect()
                if not connect_result.success:
                    return ConbusDatapointResponse(
                        success=False,
                        request=ConbusDatapointRequest(
                            datapoint_type=DatapointTypeName.UNKNOWN,  # Placeholder
                            target_serial=target_serial,
                            function_code=function_code,
                            datapoint_code=datapoint_code,
                        ),
                        error=f"Not connected to server: {connect_result.error}",
                    )

            # Send telegram
            self.socket.send(telegram.encode("latin-1"))
            self.last_activity = datetime.now()
            self.logger.info(f"Sent custom telegram: {telegram}")

            # Receive responses
            responses = self._receive_responses()

            return ConbusDatapointResponse(
                success=True,
                request=ConbusDatapointRequest(
                    datapoint_type=DatapointTypeName.UNKNOWN,  # Placeholder
                    target_serial=target_serial,
                    function_code=function_code,
                    datapoint_code=datapoint_code,
                ),
                sent_telegram=telegram,
                received_telegrams=responses,
            )

        except Exception as e:
            error_msg = f"Failed to send custom telegram: {e}"
            self.logger.error(error_msg)
            return ConbusDatapointResponse(
                success=False,
                request=ConbusDatapointRequest(
                    datapoint_type=DatapointTypeName.UNKNOWN,  # Placeholder
                    target_serial=target_serial,
                    function_code=function_code,
                    datapoint_code=datapoint_code,
                ),
                error=error_msg,
            )

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.disconnect()
