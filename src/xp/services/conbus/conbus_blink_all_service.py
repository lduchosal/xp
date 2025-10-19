"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
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
    Service for receiving telegrams from Conbus servers.

    Uses composition with ConbusService to provide receive-only functionality
    for collecting waiting event telegrams from the server.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus client send service"""
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
        self.logger.debug("Connection established, send discover telegram...")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )
        if self.progress_callback:
            self.progress_callback(".")

    def send_blink(self, serial_number: str) -> None:
        self.logger.debug("Device discovered, send blink...")

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
        system_telegram = self.telegram_service.parse_system_telegram(telegram_sent)
        self.service_response.sent_telegram = system_telegram

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:

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
        """
        Get the current auto report status for a specific module.

        Args:
            on_or_off: blink or unblink device
            finish_callback: callback function to call when the autoreport status is
            timeout_seconds: timeout in seconds

        Returns:
            ConbusAutoreportResponse with operation result and auto report status

        Raises:
            ConbusAutoreportError: If the operation fails
        """

        self.logger.info("Starting get_autoreport_status")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.on_or_off = on_or_off
        self.start_reactor()
