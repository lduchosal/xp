"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging

from xp.models import (
    ConbusDiscoverResponse,
    ConbusResponse,
)
from xp.services.conbus.conbus_service import ConbusService
from xp.services.telegram.telegram_discover_service import TelegramDiscoverService
from xp.services.telegram.telegram_service import TelegramService


class ConbusDiscoverError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusDiscoverService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        telegram_discover_service: TelegramDiscoverService,
        conbus_service: ConbusService,
    ):
        """Initialize the Conbus client send service

        Args:
            telegram_service: TelegramService for dependency injection
            telegram_discover_service: TelegramDiscoverService for dependency injection
            conbus_service: ConbusService for dependency injection
        """

        # Service dependencies
        self.telegram_service = telegram_service
        self.telegram_discover_service = telegram_discover_service
        self.conbus_service = conbus_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def send_discover_telegram(self) -> ConbusDiscoverResponse:
        """Send a telegram to the Conbus server"""

        # Generate telegram based on type
        telegram = self.telegram_discover_service.generate_discover_telegram()

        # Receive responses (with timeout)
        responses = self.conbus_service.send_raw_telegram(telegram)

        # Parse received telegrams to extract device information
        discovered_devices = self.parse_discovered_devices(responses)

        return ConbusDiscoverResponse(
            success=True,
            sent_telegram=telegram,
            received_telegrams=responses.received_telegrams,
            discovered_devices=discovered_devices,
        )

    def parse_discovered_devices(self, responses: ConbusResponse) -> list[str]:
        discovered_devices: list[str] = []
        if responses.received_telegrams is None:
            return discovered_devices
        for telegrams_str in responses.received_telegrams:
            for telegram_str in telegrams_str.split("\n"):
                try:
                    # Parse telegram using TelegramService
                    telegram_result = self.telegram_service.parse_telegram(telegram_str)
                    # Only process telegrams that have a serial_number attribute
                    if hasattr(telegram_result, "serial_number"):
                        discovered_devices.append(telegram_result.serial_number)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse telegram '{telegram_str}': {e}"
                    )
                    continue
        return discovered_devices

    def __enter__(self) -> "ConbusDiscoverService":
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException],
        _exc_val: BaseException,
        _exc_tb: object,
    ) -> None:
        # Cleanup logic if needed
        self.conbus_service.disconnect()
        pass
