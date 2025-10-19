"""Conbus Auto Report Service for getting and setting module auto report status.

This service handles auto report status operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_autoreport import ConbusAutoreportResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusAutoreportGetService(ConbusProtocol):
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
        self.finish_callback: Optional[Callable[[ConbusAutoreportResponse], None]] = (
            None
        )
        self.service_response: ConbusAutoreportResponse = ConbusAutoreportResponse(
            success=False,
            serial_number=self.serial_number,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        self.logger.debug("Connection established, retrieving autoreport status...")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(DataPointType.AUTO_REPORT_STATUS.value),
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
            self.logger.debug("Not a reply")
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )
        if (
            reply_telegram is not None
            and reply_telegram.system_function == SystemFunction.READ_DATAPOINT
            and reply_telegram.datapoint_type == DataPointType.AUTO_REPORT_STATUS
        ):
            self.logger.debug("Received autoreport status telegram")
            self.service_response.success = True
            self.service_response.timestamp = datetime.now()
            self.service_response.serial_number = self.serial_number
            self.service_response.auto_report_status = reply_telegram.data_value

            if self.finish_callback:
                self.finish_callback(self.service_response)

    def failed(self, message: str) -> None:
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def get_autoreport_status(
        self,
        serial_number: str,
        finish_callback: Callable[[ConbusAutoreportResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Get the current auto report status for a specific module.

        Args:
            serial_number: 10-digit module serial number
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
        self.finish_callback = finish_callback
        self.serial_number = serial_number
        self.start_reactor()
