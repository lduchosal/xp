"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging

from .conbus_service import ConbusService
from ..models import (
    ConbusDiscoverRequest,
    ConbusDiscoverResponse,
)
from ..services.telegram_service import TelegramService
from ..services.telegram_discovery_service import TelegramDiscoveryService


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

        # Service dependencies
        self.telegram_service = TelegramService()
        self.discovery_service = TelegramDiscoveryService()
        self.conbus_service = ConbusService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def send_telegram(self, request: ConbusDiscoverRequest) -> ConbusDiscoverResponse:
        """Send a telegram to the Conbus server"""

        # Generate telegram based on type
        telegram = self.discovery_service.generate_discovery_telegram()

        # Receive responses (with timeout)
        responses = self.conbus_service.send_raw_telegram(telegram)

        # Parse received telegrams to extract device information
        discovered_devices = []
        for telegrams_str in responses.received_telegrams:
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
            received_telegrams=responses.received_telegrams,
            discovered_devices=discovered_devices,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      # Cleanup logic if needed
        pass

