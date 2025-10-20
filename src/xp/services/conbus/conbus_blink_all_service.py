"""Conbus Blink All Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
blink/unblink telegrams to all discovered modules on the network.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_blink import ConbusBlinkResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusBlinkAllService(ConbusProtocol):
    """
    Service for blinking all modules on Conbus servers.

    Uses ConbusProtocol to provide blink/unblink functionality
    for all discovered modules on the network.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus blink all service.

        Args:
            telegram_service: Service for parsing telegrams.
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event loop.
        """
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.on_or_off = "none"
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusBlinkResponse], None]] = None
        self.service_response: ConbusBlinkResponse = ConbusBlinkResponse(
            success=False,
            serial_number=self.serial_number,
            system_function=SystemFunction.NONE,
            operation=self.on_or_off,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, send discover telegram.")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )
        if self.progress_callback:
            self.progress_callback(".")

    def send_blink(self, serial_number: str) -> None:
        """Send blink or unblink telegram to a discovered module.

        Args:
            serial_number: 10-digit module serial number.
        """
        self.logger.debug("Device discovered, send blink.")

        # Blink is 05, Unblink is 06
        system_function = SystemFunction.UNBLINK
        if self.on_or_off.lower() == "on":
            system_function = SystemFunction.BLINK

        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=system_function,
            data_value="00",
        )
        self.service_response.system_function = system_function
        self.service_response.operation = self.on_or_off

        if self.progress_callback:
            self.progress_callback(".")

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        system_telegram = self.telegram_service.parse_system_telegram(telegram_sent)
        self.service_response.sent_telegram = system_telegram

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.service_response.received_telegrams:
            self.service_response.received_telegrams = []
        self.service_response.received_telegrams.append(telegram_received.frame)

        if (
            not telegram_received.checksum_valid
            or telegram_received.telegram_type != TelegramType.REPLY
        ):
            self.logger.debug("Not a reply")
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )
        if (
            reply_telegram
            and reply_telegram.system_function == SystemFunction.DISCOVERY
        ):
            self.logger.debug("Received discovery response")
            self.send_blink(reply_telegram.serial_number)
            if self.progress_callback:
                self.progress_callback(".")
            return

        if reply_telegram and reply_telegram.system_function in (
            SystemFunction.BLINK,
            SystemFunction.UNBLINK,
        ):
            self.logger.debug("Received blink response")
            if self.progress_callback:
                self.progress_callback(".")
            return

        self.logger.debug("Received unexpected response")

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def send_blink_all_telegram(
        self,
        on_or_off: str,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusBlinkResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Send blink command to all discovered modules.

        Args:
            on_or_off: "on" to blink or "off" to unblink all devices.
            progress_callback: Callback function to call with progress updates.
            finish_callback: Callback function to call when the operation completes.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting send_blink_all_telegram")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.on_or_off = on_or_off
        self.start_reactor()
