"""Conbus Link Number Service for setting module link numbers.

This service handles setting link numbers for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusLinknumberSetService(ConbusProtocol):
    """
    Service for setting module link numbers via Conbus telegrams.

    Handles link number assignment by sending F04D04 telegrams and processing
    ACK/NAK responses from modules.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus link number set service"""
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.link_number: int = 0
        self.finish_callback: Optional[Callable[[ConbusLinknumberResponse], None]] = (
            None
        )
        self.service_response: ConbusLinknumberResponse = ConbusLinknumberResponse(
            success=False, serial_number=self.serial_number, result=""
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        self.logger.debug(
            f"Connection established, setting link number {self.link_number}..."
        )

        # Validate parameters before sending
        if not self.serial_number or len(self.serial_number) != 10:
            self.failed(f"Serial number must be 10 digits, got: {self.serial_number}")
            return

        if not (0 <= self.link_number <= 99):
            self.failed(f"Link number must be between 0-99, got: {self.link_number}")
            return

        # Send F04D04{link_number} telegram
        # F04 = WRITE_CONFIG, D04 = LINK_NUMBER datapoint type
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.WRITE_CONFIG,
            data_value=f"{DataPointType.LINK_NUMBER.value}{self.link_number:02d}",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        self.service_response.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
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
        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )

        if not reply_telegram:
            self.logger.debug("Failed to parse reply telegram")
            return

        # Check for ACK or NAK response
        if reply_telegram.system_function == SystemFunction.ACK:
            self.logger.debug("Received ACK response")
            self.succeed(SystemFunction.ACK)
        elif reply_telegram.system_function == SystemFunction.NAK:
            self.logger.debug("Received NAK response")
            self.failed("Module responded with NAK")
        else:
            self.logger.debug(
                f"Unexpected system function: {reply_telegram.system_function}"
            )

    def succeed(self, system_function: SystemFunction) -> None:
        self.logger.debug("Successfully set link number")
        self.service_response.success = True
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.result = "ACK"
        self.service_response.link_number = self.link_number
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def failed(self, message: str) -> None:
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.result = "NAK"
        self.service_response.error = message
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def set_linknumber(
        self,
        serial_number: str,
        link_number: int,
        finish_callback: Callable[[ConbusLinknumberResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Set the link number for a specific module.

        Args:
            serial_number: 10-digit module serial number
            link_number: Link number to set (0-99)
            finish_callback: Callback function to call when operation completes
            timeout_seconds: Optional timeout in seconds
        """
        self.logger.info("Starting set_linknumber")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.link_number = link_number
        self.finish_callback = finish_callback
        self.start_reactor()
