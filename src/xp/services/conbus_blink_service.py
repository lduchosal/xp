"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging

from . import TelegramService
from .conbus_service import ConbusService
from .conbus_discover_service import ConbusDiscoverService
from .telegram_blink_service import TelegramBlinkService
from ..models.conbus_blink import ConbusBlinkResponse
from ..models.system_function import SystemFunction

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


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      # Cleanup logic if needed
        pass

    def send_blink_telegram(self, serial_number: str, on_or_off: str) -> ConbusBlinkResponse:
        """
        Send blink command to start blinking module LED.

        Examples:

        \b
            xp conbus blink 0020044964 on
            xp conbus blink 0020044964 off
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
            if response.success and len(response.received_telegrams) > 0:
                ack_or_nak = response.received_telegrams[0]
                reply_telegram = self.telegram_service.parse_telegram(ack_or_nak)

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
        # First discover all devices
        with self.discover_service:
            discover_response = self.discover_service.send_discover_telegram()

        if not discover_response.success:
            return ConbusBlinkResponse(
                success=False,
                serial_number="all",
                operation=on_or_off,
                system_function=SystemFunction.BLINK if on_or_off == "on" else SystemFunction.UNBLINK,
                error="Failed to discover devices",
            )

        # If no devices discovered, return success with appropriate message
        if not discover_response.discovered_devices:
            return ConbusBlinkResponse(
                success=True,
                serial_number="all",
                operation=on_or_off,
                system_function=SystemFunction.BLINK if on_or_off == "on" else SystemFunction.UNBLINK,
                error="No devices discovered",
            )

        # Send blink command to each discovered device
        all_success = True
        all_blink_telegram = []

        for serial_number in discover_response.discovered_devices:
            blink_telegram = self.telegram_blink_service.generate_blink_telegram(serial_number, on_or_off)
            all_blink_telegram.append(blink_telegram)

        response = self.conbus_service.send_raw_telegrams(all_blink_telegram)
        if not response.success:
            all_success = False

        return ConbusBlinkResponse(
            success=all_success,
            serial_number="all",
            operation=on_or_off,
            system_function=SystemFunction.BLINK if on_or_off == "on" else SystemFunction.UNBLINK,
            received_telegrams=response.received_telegrams,
        )
