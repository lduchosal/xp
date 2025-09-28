"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
import socket
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any

import yaml
from typing_extensions import Callable

from .conbus_connection_pool import ConbusConnectionPool
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
        self.is_connected = False
        self.last_activity: Optional[datetime] = None

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self._load_config()

        # Initialize connection pool
        self._connection_pool = ConbusConnectionPool.get_instance()
        self._connection_pool.initialize(self.config)

    def _load_config(self) -> None:
        """Load client configuration from cli.yml"""
        try:
            if Path(self.config_path).exists():
                with Path(self.config_path).open("r") as file:
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
        """Test connection using the connection pool"""
        try:
            # Test connection by acquiring and immediately releasing
            with self._connection_pool:
                self.is_connected = True
                self.last_activity = datetime.now()

                self.logger.info(
                    f"Connection pool ready for {self.config.ip}:{self.config.port}"
                )

                return Response(
                    success=True,
                    data={
                        "message": f"Connection pool ready for {self.config.ip}:{self.config.port}",
                        "config": self.config.to_dict(),
                    },
                    error=None,
                )

        except Exception as e:
            error_msg = f"Failed to establish connection pool to {self.config.ip}:{self.config.port}: {e}"
            self.logger.error(error_msg)
            self.is_connected = False
            return Response(success=False, data=None, error=error_msg)

    def disconnect(self) -> None:
        """Close connection pool (graceful shutdown)"""
        try:
            self._connection_pool.close()
            self.logger.info("Connection pool closed")
        except Exception as e:
            self.logger.error(f"Error closing connection pool: {e}")
        finally:
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
        telegrams: list[str] = []
        if not raw_data:
            return telegrams

        # Find all telegram patterns <...>
        start_pos = 0
        while True:
            # Find the start of next telegram
            start_idx = raw_data.find("<", start_pos)
            if start_idx == -1:
                break

            # Find the end of this telegram
            end_idx = raw_data.find(">", start_idx)
            if end_idx == -1:
                # Incomplete telegram at the end
                break

            # Extract telegram including < and >
            telegram = raw_data[start_idx : end_idx + 1]
            if telegram.strip():
                telegrams.append(telegram.strip())

            start_pos = end_idx + 1

        return telegrams

    def receive_responses(
        self,
        timeout: float = 0.1,
        receive_callback: Optional[Callable[[list[str]], None]] = None,
    ) -> List[str]:
        """Receive responses from the server and properly split telegrams"""
        import time

        all_telegrams = []
        start_time = time.time()

        try:
            with self._connection_pool as connection:
                while time.time() - start_time < timeout:
                    # Call _receive_responses_with_connection with a short timeout for each iteration
                    telegrams = self._receive_responses_with_connection(
                        connection, timeout=0.1
                    )
                    if receive_callback is not None:
                        receive_callback(telegrams)
                    all_telegrams.extend(telegrams)

                    # Small sleep to avoid busy waiting when no data
                    time.sleep(0.01)
        except Exception as e:
            self.logger.error(f"Error receiving responses: {e}")
            return []

        return all_telegrams

    def _receive_responses_with_connection(
        self,
        connection: socket.socket,
        timeout: float = 1.0,
        receive_callback: Optional[Callable[[list[str]], None]] = None,
    ) -> List[str]:
        """Receive responses from the server using a specific connection"""
        accumulated_data = ""

        try:
            # Set a shorter timeout for receiving responses
            original_timeout = connection.gettimeout()
            connection.settimeout(timeout)  # 1 second timeout for responses

            while True:
                try:
                    data = connection.recv(1024)
                    if not data:
                        break

                    # Accumulate all received data
                    message = data.decode("latin-1")
                    if receive_callback is not None:
                        parsed_telegrams = self._parse_telegrams(message)
                        receive_callback(parsed_telegrams)
                    accumulated_data += message
                    self.last_activity = datetime.now()
                    connection.settimeout(0.1)  # 2 second timeout for responses

                except socket.timeout:
                    # No more data available
                    break

            # Restore original timeout
            connection.settimeout(original_timeout)

        except Exception as e:
            self.logger.error(f"Error receiving responses: {e}")

        # Parse telegrams from accumulated data
        telegrams = self._parse_telegrams(accumulated_data)
        for telegram in telegrams:
            self.logger.info(f"Received telegram: {telegram}")

        return telegrams

    def send_telegram(
        self,
        serial_number: str,
        system_function: SystemFunction,
        data: str,
        receive_callback: Optional[Callable[[list[str]], None]] = None,
    ) -> ConbusResponse:
        """Send custom telegram with specified function and data point codes"""
        # Generate custom system telegram: <S{serial}F{function}{data_point}{checksum}>
        function_code = system_function.value
        telegram_body = f"S{serial_number}F{function_code}D{data}"
        checksum = calculate_checksum(telegram_body)
        telegram = f"<{telegram_body}{checksum}>"

        return self.send_raw_telegram(telegram, receive_callback)

    def send_telegram_body(
        self,
        telegram_body: str,
        receive_callback: Optional[Callable[[list[str]], None]] = None,
    ) -> ConbusResponse:
        """Send custom telegram with specified function and data point codes"""
        checksum = calculate_checksum(telegram_body)
        telegram = f"<{telegram_body}{checksum}>"

        return self.send_raw_telegram(telegram, receive_callback)

    def send_raw_telegram(
        self,
        telegram: Optional[str] = None,
        receive_callback: Optional[Callable[[list[str]], None]] = None,
    ) -> ConbusResponse:
        """Send telegram using connection pool with automatic acquire/release"""
        request = ConbusRequest(telegram=telegram)

        try:
            # Use context manager for automatic connection management
            with self._connection_pool as connection:

                # Draining event waiting to be read (wait time 0)
                responses = self._receive_responses_with_connection(connection, 0.001)
                self.logger.info(f"Purged telegram: {responses}")

                # Send telegram
                if telegram is not None:
                    connection.send(telegram.encode("latin-1"))
                    self.logger.info(f"Sent telegram: {telegram}")

                self.last_activity = datetime.now()
                self.is_connected = True  # Update connection status

                # Receive responses
                responses = self._receive_responses_with_connection(
                    connection, 0.1, receive_callback
                )

                return ConbusResponse(
                    success=True,
                    request=request,
                    sent_telegram=telegram,
                    received_telegrams=responses,
                )
                # Connection automatically released here

        except Exception as e:
            error_msg = f"Failed to send telegram: {e}"
            self.logger.error(error_msg)
            self.is_connected = False  # Update connection status on error
            return ConbusResponse(
                success=False,
                request=request,
                error=error_msg,
            )

    def send_raw_telegrams(self, telegrams: List[str]) -> ConbusResponse:
        self.logger.info(f"send_raw_telegrams: {telegrams}")
        all_telegrams = "".join(telegrams)
        return self.send_raw_telegram(all_telegrams)

    def __enter__(self) -> "ConbusService":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit - ensure connection is closed"""
        self.disconnect()
