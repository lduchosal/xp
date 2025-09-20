"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging

from . import TelegramService
from .conbus_service import ConbusService
from .telegram_blink_service import BlinkService
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
        self.blink_service = BlinkService()
        self.telegram_service = TelegramService()

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
