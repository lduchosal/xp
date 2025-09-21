"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import socket
import logging
import yaml
import os
from typing import List, Optional
from datetime import datetime

from ..models import (
    ConbusClientConfig,
    ConbusRequest,
    ConbusResponse,
    ConbusConnectionStatus,
)
from ..models.response import Response
from ..models.system_function import SystemFunction
from ..utils.checksum import calculate_checksum


class ConbusError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusService:
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

    @staticmethod
    def _parse_telegrams(raw_data: str) -> List[str]:
        """Parse raw data and extract telegrams using < and > delimiters"""
        telegrams = []
        if not raw_data:
            return telegrams

        # Find all telegram patterns <...>
        start_pos = 0
        while True:
            # Find the start of next telegram
            start_idx = raw_data.find('<', start_pos)
            if start_idx == -1:
                break

            # Find the end of this telegram
            end_idx = raw_data.find('>', start_idx)
            if end_idx == -1:
                # Incomplete telegram at the end
                break

            # Extract telegram including < and >
            telegram = raw_data[start_idx:end_idx + 1]
            if telegram.strip():
                telegrams.append(telegram.strip())

            start_pos = end_idx + 1

        return telegrams

    def _receive_responses(self) -> List[str]:
        """Receive responses from the server and properly split telegrams"""
        accumulated_data = ""

        try:
            # Set a shorter timeout for receiving responses
            original_timeout = self.socket.gettimeout()
            self.socket.settimeout(2.0)  # 2 second timeout for responses

            while True:
                try:
                    data = self.socket.recv(1024)
                    if not data:
                        break

                    # Accumulate all received data
                    message = data.decode("latin-1")
                    accumulated_data += message
                    self.last_activity = datetime.now()

                except socket.timeout:
                    # No more data available
                    break

            # Restore original timeout
            self.socket.settimeout(original_timeout)

        except Exception as e:
            self.logger.error(f"Error receiving responses: {e}")

        # Parse telegrams from accumulated data
        telegrams = self._parse_telegrams(accumulated_data)
        for telegram in telegrams:
            self.logger.info(f"Received telegram: {telegram}")

        return telegrams

    def send_telegram(
        self, serial_number: str, system_function: SystemFunction, data: str
    ) -> ConbusResponse:
        """Send custom telegram with specified function and data point codes"""
        # Generate custom system telegram: <S{serial}F{function}{data_point}{checksum}>
        function_code = system_function.value
        telegram_body = f"S{serial_number}F{function_code}D{data}"
        checksum = calculate_checksum(telegram_body)
        telegram = f"<{telegram_body}{checksum}>"

        return  self.send_raw_telegram(telegram)

    def send_telegram_body(
        self, telegram_body: str
    ) -> ConbusResponse:
        """Send custom telegram with specified function and data point codes"""
        checksum = calculate_checksum(telegram_body)
        telegram = f"<{telegram_body}{checksum}>"

        return self.send_raw_telegram(telegram)

    def send_raw_telegram(
            self, telegram: Optional[str] = None
    ) -> ConbusResponse:
        """Send custom telegram with specified function and data point codes"""
        # Generate custom system telegram: <S{serial}F{function}{data_point}{checksum}>

        request = ConbusRequest(
            telegram=telegram,
        )
        try:
            if not self.is_connected:
                connect_result = self.connect()
                if not connect_result.success:
                    return ConbusResponse(
                        success=False,
                        request=request,
                        error=f"Not connected to server: {connect_result.error}",
                    )

            # Send telegram
            if telegram is not None:
                self.socket.send(telegram.encode("latin-1"))
                self.logger.info(f"Sent custom telegram: {telegram}")

            self.last_activity = datetime.now()

            # Receive responses
            responses = self._receive_responses()

            return ConbusResponse(
                success=True,
                request=request,
                sent_telegram=telegram,
                received_telegrams=responses,
            )

        except Exception as e:
            error_msg = f"Failed to send custom telegram: {e}"
            self.logger.error(error_msg)
            return ConbusResponse(
                success=False,
                request=request,
                error=error_msg,
            )

    def send_raw_telegrams(self, telegrams: List[str]) -> ConbusResponse:
        self.logger.info(f"send_raw_telegrams: {telegrams}")
        all_telegrams = "".join(telegrams)
        return self.send_raw_telegram(all_telegrams)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.disconnect()

