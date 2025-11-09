"""Conbus Datapoint Service for querying module datapoints.

This service handles datapoint query operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig, ConbusDatapointResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusDatapointService(ConbusProtocol):
    """
    Service for querying datapoints from Conbus modules.

    Uses ConbusProtocol to provide datapoint query functionality
    for reading sensor data and module information.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus datapoint service.

        Args:
            telegram_service: Service for parsing telegrams.
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event loop.
        """
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.datapoint_type: Optional[DataPointType] = None
        self.datapoint_finished_callback: Optional[
            Callable[[ConbusDatapointResponse], None]
        ] = None
        self.service_response: ConbusDatapointResponse = ConbusDatapointResponse(
            success=False,
            serial_number=self.serial_number,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            f"Connection established, querying datapoint {self.datapoint_type}."
        )
        if self.datapoint_type is None:
            self.failed("Datapoint type not set")
            return

        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(self.datapoint_type.value),
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
        datapoint_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )

        if (
            not datapoint_telegram
            or datapoint_telegram.system_function != SystemFunction.READ_DATAPOINT
            or datapoint_telegram.datapoint_type != self.datapoint_type
        ):
            self.logger.debug("Not a reply for our datapoint type")
            return

        self.logger.debug("Received datapoint telegram")
        self.succeed(datapoint_telegram)

    def succeed(self, datapoint_telegram: ReplyTelegram) -> None:
        """Handle successful datapoint query.

        Args:
            datapoint_telegram: The parsed datapoint telegram.
        """
        self.logger.debug("Succeed querying datapoint")
        self.service_response.success = True
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.system_function = SystemFunction.READ_DATAPOINT
        self.service_response.datapoint_type = self.datapoint_type
        self.service_response.datapoint_telegram = datapoint_telegram
        self.service_response.data_value = datapoint_telegram.data_value
        if self.datapoint_finished_callback:
            self.datapoint_finished_callback(self.service_response)
        self._stop_reactor()

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.error = message
        if self.datapoint_finished_callback:
            self.datapoint_finished_callback(self.service_response)

    def query_datapoint(
        self,
        serial_number: str,
        datapoint_type: DataPointType,
        finish_callback: Callable[[ConbusDatapointResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Query a specific datapoint from a module.

        Args:
            serial_number: 10-digit module serial number.
            datapoint_type: Type of datapoint to query.
            finish_callback: Callback function to call when the datapoint is received.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting query_datapoint")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.datapoint_finished_callback = finish_callback
        self.serial_number = serial_number
        self.datapoint_type = datapoint_type
        self.start_reactor()
