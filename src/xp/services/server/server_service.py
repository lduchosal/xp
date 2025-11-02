"""Conbus Server Service for emulating device discover responses.

This service implements a TCP server that listens on port 10001 and responds to
Discover Request telegrams with configurable device information.
"""

import logging
import socket
import threading
from pathlib import Path
from typing import Dict, List, Optional

from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.server.base_server_service import BaseServerService
from xp.services.server.device_service_factory import DeviceServiceFactory
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_service import TelegramService


class ServerError(Exception):
    """Raised when Conbus server operations fail."""

    pass


class ServerService:
    """
    Main TCP server implementation for Conbus device emulation.

    Manages TCP socket lifecycle, handles client connections,
    parses Discover Request telegrams, and coordinates device responses.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        discover_service: TelegramDiscoverService,
        device_factory: DeviceServiceFactory,
        config_path: str = "server.yml",
        port: int = 10001,
    ):
        """Initialize the Conbus server service.

        Args:
            telegram_service: Service for parsing system telegrams.
            discover_service: Service for handling discover requests.
            device_factory: Factory for creating device service instances (injected via DI).
            config_path: Path to the server configuration file.
            port: TCP port to listen on.
        """
        self.telegram_service = telegram_service
        self.discover_service = discover_service
        self.device_factory = device_factory
        self.config_path = config_path
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.devices: List[ConsonModuleConfig] = []
        self.device_services: Dict[str, BaseServerService] = (
            {}
        )  # serial -> device service instance

        # Collect device buffer to broadcast to client
        self.collector_thread: Optional[threading.Thread] = (
            None  # Background thread for storm
        )
        self.collector_stop_event = threading.Event()  # Event to stop thread
        self.collector_buffer: list[str] = []  # All collected buffers

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load device configuration
        self._load_device_config()

    def _load_device_config(self) -> None:
        """Load device configurations from server.yml."""
        try:
            if Path(self.config_path).exists():
                config = ConsonModuleListConfig.from_yaml(self.config_path)
                self.devices = [module for module in config.root if module.enabled]
                self._create_device_services()
                self.logger.info(f"Loaded {len(self.devices)} devices from config")
            else:
                self.logger.warning(
                    f"Config file {self.config_path} not found, using empty device list"
                )
                self.devices = []
                self.device_services = {}
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            self.devices = []
            self.device_services = {}

    def _create_device_services(self) -> None:
        """Create device service instances based on device configuration."""
        self.device_services = {}

        for module in self.devices:
            module_type = module.module_type
            serial_number = module.serial_number

            try:
                # Use factory to create device instance
                self.device_services[serial_number] = self.device_factory.create_device(
                    module_type, serial_number
                )

            except ValueError as e:
                # Factory raises ValueError for unknown device types
                self.logger.warning(str(e))

            except Exception as e:
                self.logger.error(
                    f"Error creating device service for {serial_number}: {e}"
                )

    def start_server(self) -> None:
        """Start the TCP server on port 10001.

        Raises:
            ServerError: If server is already running or fails to start.
        """
        if self.is_running:
            raise ServerError("Server is already running")

        try:
            # Create TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to port 10001 on all interfaces
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(1)  # Accept single connection as per spec

            self._start_device_collector_thread()

            self.is_running = True
            self.logger.info(f"Conbus emulator server started on port {self.port}")
            self.logger.info(
                f"Configured devices: {list([device.serial_number for device in self.devices])}"
            )

            # Start accepting connections
            self._accept_connections()

        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise ServerError(f"Failed to start server: {e}")

    def stop_server(self) -> None:
        """Stop the TCP server."""
        if not self.is_running:
            return

        self.is_running = False

        if self.server_socket:
            try:
                self.server_socket.close()
                self.logger.info("Conbus emulator server stopped")
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")

    def _accept_connections(self) -> None:
        """Accept and handle client connections."""
        while self.is_running:
            try:
                # Accept connection
                if self.server_socket is None:
                    break
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"Client connected from {client_address}")

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client, args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")
                break

    def _handle_client(
        self, client_socket: socket.socket, client_address: tuple[str, int]
    ) -> None:
        """Handle individual client connection."""
        try:

            idle_timeout = 300
            rcv_timeout = 10

            # Set timeout for idle connections (30 seconds as per spec)
            client_socket.settimeout(rcv_timeout)
            timeout = idle_timeout / rcv_timeout

            while True:

                # send waiting buffer
                for i in range(len(self.collector_buffer)):
                    buffer = self.collector_buffer.pop()
                    client_socket.send(buffer.encode("latin-1"))
                    self.logger.debug(f"Sent buffer to {client_address}")

                # Receive data from client
                data = None
                try:
                    data = client_socket.recv(1024)
                except socket.timeout:
                    pass
                finally:
                    timeout -= 1

                if not data:
                    if timeout <= 0:
                        break
                    continue

                # reset timeout on receiving data
                timeout = idle_timeout / rcv_timeout

                message = data.decode("latin-1").strip()
                self.logger.debug(f"Received from {client_address}: {message}")

                # Process request (discover or data request)
                responses = self._process_request(message)

                # Send responses
                for response in responses:
                    client_socket.send(response.encode("latin-1"))
                    self.logger.debug(f"Sent to {client_address}: {response[:-1]}")

        except socket.timeout:
            self.logger.debug(f"Client {client_address} timed out")
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
        finally:
            try:
                client_socket.close()
                self.logger.info(f"Client {client_address} disconnected")
            except Exception as e:
                self.logger.error(f"Error closing client socket: {e}")

    def _process_request(self, message: str) -> List[str]:
        """Process incoming request and generate responses.

        Args:
            message: Message potentially containing multiple telegrams in format <TELEGRAM><TELEGRAM2>...

        Returns:
            List of responses for all processed telegrams.
        """
        responses: list[str] = []

        try:
            # Split message into individual telegrams (enclosed in angle brackets)
            telegrams = self._split_telegrams(message)

            if not telegrams:
                self.logger.warning(f"No valid telegrams found in message: {message}")
                return responses

            # Process each telegram
            for telegram in telegrams:
                telegram_responses = self._process_single_telegram(telegram)
                responses.extend(telegram_responses)

        except Exception as e:
            self.logger.error(f"Error processing request: {e}")

        return responses

    def _split_telegrams(self, message: str) -> List[str]:
        """Split message into individual telegrams.

        Args:
            message: Raw message containing one or more telegrams in format <TELEGRAM><TELEGRAM2>...

        Returns:
            List of individual telegram strings including angle brackets.
        """
        telegrams = []
        start = 0

        while True:
            # Find the start of a telegram
            start_idx = message.find("<", start)
            if start_idx == -1:
                break

            # Find the end of the telegram
            end_idx = message.find(">", start_idx)
            if end_idx == -1:
                self.logger.warning(
                    f"Incomplete telegram found starting at position {start_idx}"
                )
                break

            # Extract telegram including angle brackets
            telegram = message[start_idx : end_idx + 1]
            telegrams.append(telegram)

            # Move to the next position
            start = end_idx + 1

        return telegrams

    def _process_single_telegram(self, telegram: str) -> List[str]:
        """Process a single telegram and generate responses.

        Args:
            telegram: A single telegram string.

        Returns:
            List of response strings for this telegram.
        """
        responses: list[str] = []

        try:
            # Parse the telegram
            parsed_telegram = self.telegram_service.parse_system_telegram(telegram)

            if not parsed_telegram:
                self.logger.warning(f"Failed to parse telegram: {telegram}")
                return responses

            # Handle discover requests
            if self.discover_service.is_discover_request(parsed_telegram):
                for device_service in self.device_services.values():
                    discover_response = device_service.generate_discover_response()
                    responses.append(f"{discover_response}\n")
            else:
                # Handle data requests for specific devices
                serial_number = parsed_telegram.serial_number

                # If broadcast (0000000000), respond from all devices
                if serial_number == "0000000000":
                    for device_service in self.device_services.values():
                        broadcast_response: Optional[str] = (
                            device_service.process_system_telegram(parsed_telegram)
                        )
                        if broadcast_response:
                            responses.append(f"{broadcast_response}\n")
                # If specific device - lookup by string serial number
                else:
                    if serial_number in self.device_services:
                        device_service = self.device_services[serial_number]
                        device_response: Optional[str] = (
                            device_service.process_system_telegram(parsed_telegram)
                        )
                        if device_response:
                            responses.append(f"{device_response}\n")
                    else:
                        self.logger.debug(
                            f"No device found for serial: {serial_number}"
                        )

        except Exception as e:
            self.logger.error(f"Error processing telegram: {e}")

        return responses

    def get_server_status(self) -> dict:
        """Get current server status.

        Returns:
            Dictionary containing server status information.
        """
        return {
            "running": self.is_running,
            "port": self.port,
            "devices_configured": len(self.devices),
            "device_list": list([device.serial_number for device in self.devices]),
        }

    def reload_config(self) -> None:
        """Reload device configuration from file."""
        self._load_device_config()
        self.logger.info(
            f"Configuration reloaded: {len(self.devices)} devices, {len(self.device_services)} services"
        )

    def _start_device_collector_thread(self) -> None:
        """Start device buffer collector thread."""
        if self.collector_thread and self.collector_thread.is_alive():
            self.logger.debug("Collector thread already running")
            return

        # Start background thread to send storm telegrams
        self.collector_thread = threading.Thread(
            target=self._device_collector_thread, daemon=True, name="DeviceCollector"
        )
        self.collector_thread.start()
        self.logger.info("Collector thread started")

    def _stop_device_collector_thread(self) -> None:
        """Stop device buffer collector thread."""
        if not self.collector_thread or not self.collector_thread.is_alive():
            self.logger.debug("Collector thread not running")
            return

        self.logger.info(f"Stopping collector thread: {self.collector_thread.name}")

        # Wait for thread to finish (with timeout)
        if self.collector_thread and self.collector_thread.is_alive():
            self.collector_thread.join(timeout=1.0)

            self.logger.info("Collector stopped.")

    def _device_collector_thread(self) -> None:
        """Device buffer collector thread."""
        self.logger.info("Collector thread starting")

        while True:
            collected = 0
            for device_service in self.device_services.values():
                telegram_buffer = device_service.collect_telegram_buffer()
                self.collector_buffer.extend(telegram_buffer)
                collected += len(telegram_buffer)

            # Wait a bit before checking again
            self.collector_stop_event.wait(timeout=1)
