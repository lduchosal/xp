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

from .telegram_blink_service import BlinkService
from ..models import (
    ConbusClientConfig,
    ConbusDiscoverRequest,
    ConbusDiscoverResponse,
    ConbusConnectionStatus,
)
from ..models.response import Response
from ..services.telegram_service import TelegramService
from ..services.telegram_discovery_service import TelegramDiscoveryService
from ..services.telegram_version_service import VersionService
from ..utils.checksum import calculate_checksum


class ConbusDiscoverError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusDiscoverService:
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
        self.discovery_service = TelegramDiscoveryService()

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

    def send_telegram(self, request: ConbusDiscoverRequest) -> ConbusDiscoverResponse:
        """Send a telegram to the Conbus server"""
        if not self.is_connected:
            # Try to connect automatically
            connect_result = self.connect()
            if not connect_result.success:
                return ConbusDiscoverResponse(
                    success=False,
                    request=request,
                    error=f"Not connected to server: {connect_result.error}",
                )

        try:
            # Generate telegram based on type
            telegram = self.discovery_service.generate_discovery_telegram()
            if not telegram:
                return ConbusDiscoverResponse(
                    success=False,
                    request=request,
                    error=f"Failed to generate telegram for type discover",
                )

            # Send telegram
            self.socket.send(telegram.encode("latin-1"))
            self.last_activity = datetime.now()

            self.logger.info(f"Sent telegram: {telegram}")

            # Receive responses (with timeout)
            responses = self._receive_responses()

            # Parse received telegrams to extract device information
            discovered_devices = []
            for telegrams_str in responses:
                for telegram_str in telegrams_str.split("\n"):
                    try:
                        # Parse telegram using TelegramService
                        telegram_result = self.telegram_service.parse_telegram(telegram_str)
                        discovered_devices.append(telegram_result.serial_number)

                    except Exception as e:
                        self.logger.warning(f"Failed to parse telegram '{telegram_str}': {e}")
                        continue

            return ConbusDiscoverResponse(
                success=True,
                request=request,
                sent_telegram=telegram,
                received_telegrams=responses,
                discovered_devices=discovered_devices,
            )

        except socket.timeout:
            error_msg = "Response timeout"
            self.logger.error(error_msg)
            return ConbusDiscoverResponse(success=False, request=request, error=error_msg)
        except Exception as e:
            error_msg = f"Failed to send telegram: {e}"
            self.logger.error(error_msg)
            return ConbusDiscoverResponse(success=False, request=request, error=error_msg)

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

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.disconnect()
