"""Conbus Custom Service for sending custom telegrams to modules.

This service handles custom telegram operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_custom import ConbusCustomResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusCustomService(ConbusProtocol):
    """
    Service for sending custom telegrams to Conbus modules.

    Uses ConbusProtocol to provide custom telegram functionality
    for sending arbitrary function codes and data to modules.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus custom service.

        Args:
            telegram_service: Service for parsing telegrams.
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event loop.
        """
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.function_code: str = ""
        self.data: str = ""
        self.finish_callback: Optional[Callable[[ConbusCustomResponse], None]] = None
        self.service_response: ConbusCustomResponse = ConbusCustomResponse(
            success=False,
            serial_number=self.serial_number,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            f"Connection established, sending custom telegram F{self.function_code}D{self.data}."
        )
        system_function = SystemFunction.from_code(self.function_code)
        if not system_function:
            self.logger.debug(f"Invalid function code F{self.function_code}")
            self.failed(f"Invalid function code {self.function_code}")
            return

        self.send_telegram(
            serial_number=self.serial_number,
            telegram_type=TelegramType.SYSTEM,
            system_function=system_function,
            data_value=self.data,
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.sent_telegram = telegram_sent

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
            or telegram_received.serial_number != self.serial_number
        ):
            self.logger.debug("Not a reply for our serial number")
            return

        # Parse the reply telegram
        parsed_telegram = self.telegram_service.parse_telegram(telegram_received.frame)
        reply_telegram = None
        if isinstance(parsed_telegram, ReplyTelegram):
            reply_telegram = parsed_telegram

        self.logger.debug("Received reply telegram")
        self.service_response.success = True
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.function_code = self.function_code
        self.service_response.data = self.data
        self.service_response.reply_telegram = reply_telegram

        if self.finish_callback:
            self.finish_callback(self.service_response)

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

    def send_custom_telegram(
        self,
        serial_number: str,
        function_code: str,
        data: str,
        finish_callback: Callable[[ConbusCustomResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Send a custom telegram to a module.

        Args:
            serial_number: 10-digit module serial number.
            function_code: Function code (e.g., "02", "17").
            data: Data code (e.g., "E2", "AA").
            finish_callback: Callback function to call when the reply is received.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting send_custom_telegram")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.finish_callback = finish_callback
        self.serial_number = serial_number
        self.function_code = function_code
        self.data = data
        self.start_reactor()
