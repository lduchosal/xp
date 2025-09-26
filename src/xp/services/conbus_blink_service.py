"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
from typing import Any, Optional

from . import TelegramService
from .conbus_service import ConbusService
from .conbus_discover_service import ConbusDiscoverService
from .telegram_blink_service import TelegramBlinkService
from ..models.conbus_blink import ConbusBlinkResponse
from ..models.system_function import SystemFunction
from ..models.reply_telegram import ReplyTelegram


class ConbusBlinkService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus client send service"""

        # Service dependencies
        self.conbus_service = ConbusService(config_path)
        self.discover_service = ConbusDiscoverService(config_path)
        self.blink_service = TelegramBlinkService()
        self.telegram_service = TelegramService()
        self.telegram_blink_service = TelegramBlinkService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> "ConbusBlinkService":
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        # Cleanup logic if needed
        pass

    def send_blink_telegram(
        self, serial_number: str, on_or_off: str
    ) -> ConbusBlinkResponse:
        """
        Send blink command to start blinking module LED.

        Examples:

        \b
            xp conbus blink 0012345008 on
            xp conbus blink 0012345008 off
        """
        # Blink is 05, Unblink is 06
        system_function = SystemFunction.UNBLINK
        if on_or_off.lower() == "on":
            system_function = SystemFunction.BLINK

        # Send blink telegram using custom method (F05D00)
        with self.conbus_service:

            response = self.conbus_service.send_telegram(
                serial_number,
                system_function,  # Blink or Unblink function code
                "00",  # Status data point
            )

            reply_telegram = None
            if (
                response.success
                and response.received_telegrams is not None
                and len(response.received_telegrams) > 0
            ):
                ack_or_nak = response.received_telegrams[0]
                parsed_telegram = self.telegram_service.parse_telegram(ack_or_nak)
                if isinstance(parsed_telegram, ReplyTelegram):
                    reply_telegram = parsed_telegram

            return ConbusBlinkResponse(
                serial_number=serial_number,
                operation=on_or_off,
                system_function=system_function,
                response=response,
                reply_telegram=reply_telegram,
                success=response.success,
                timestamp=response.timestamp,
            )

    def blink_all(self, on_or_off: str) -> ConbusBlinkResponse:
        """
        Send blink command to all discovered devices.

        Args:
            on_or_off: "on" or "off" to control blink state

        Returns:
            ConbusBlinkResponse: Aggregated response for all devices
        """
        # Use a single ConbusService instance for both discover and blinking
        # to avoid connection conflicts
        with self.conbus_service:
            # First discover all devices using the same connection
            telegram = (
                self.discover_service.telegram_discover_service.generate_discover_telegram()
            )
            discover_responses = self.conbus_service.send_raw_telegram(telegram)

            if not discover_responses.success:
                return ConbusBlinkResponse(
                    success=False,
                    serial_number="all",
                    operation=on_or_off,
                    system_function=(
                        SystemFunction.BLINK
                        if on_or_off == "on"
                        else SystemFunction.UNBLINK
                    ),
                    error="Failed to discover devices",
                )

            # Parse received telegrams to extract device information
            discovered_devices = self.discover_service.parse_discovered_devices(
                discover_responses
            )

            # If no devices discovered, return success with appropriate message
            if not discovered_devices:
                return ConbusBlinkResponse(
                    success=True,
                    serial_number="all",
                    operation=on_or_off,
                    system_function=(
                        SystemFunction.BLINK
                        if on_or_off == "on"
                        else SystemFunction.UNBLINK
                    ),
                    error="No devices discovered",
                )

            # Send blink command to each discovered device
            all_blink_telegram = []
            for serial_number in discovered_devices:
                blink_telegram = self.telegram_blink_service.generate_blink_telegram(
                    serial_number, on_or_off
                )
                all_blink_telegram.append(blink_telegram)

            # Send all blink telegrams using the same connection
            response = self.conbus_service.send_raw_telegrams(all_blink_telegram)

            return ConbusBlinkResponse(
                success=response.success,
                serial_number="all",
                operation=on_or_off,
                system_function=(
                    SystemFunction.BLINK
                    if on_or_off == "on"
                    else SystemFunction.UNBLINK
                ),
                received_telegrams=response.received_telegrams,
            )
