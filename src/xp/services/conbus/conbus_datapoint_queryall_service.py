"""
Conbus DataPoint Query All Service.

This module provides service for querying all datapoint types from a module.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from psygnal import Signal

from xp.models import ConbusDatapointResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services import TelegramService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConbusDatapointQueryAllService:
    """
    Utility service for querying all datapoints from a module.

    This service orchestrates multiple ConbusDatapointService calls to query
    all available datapoint types sequentially.

    Attributes:
        conbus_protocol: ConbusEventProtocol for protocol communication.
        telegram_service: TelegramService for dependency injection.
        on_progress: Signal emitted for each datapoint response received.
        on_finish: Signal emitted when all datapoints queried (with response).
    """

    on_progress: Signal = Signal(ReplyTelegram)
    on_finish: Signal = Signal(ConbusDatapointResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_service: TelegramService,
    ) -> None:
        """
        Initialize the query all service.

        Args:
            conbus_protocol: ConbusEventProtocol for protocol communication.
            telegram_service: TelegramService for dependency injection.
        """
        self.conbus_protocol = conbus_protocol
        self.telegram_service = telegram_service

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        self.serial_number: str = ""
        self.service_response: ConbusDatapointResponse = ConbusDatapointResponse(
            success=False,
            serial_number=self.serial_number,
        )
        self.datapoint_types = list(DataPointType)
        self.current_index = 0

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, querying datapoints.")
        self.next_datapoint()

    def next_datapoint(self) -> bool:
        """
        Query the next datapoint type.

        Returns:
            True if there are more datapoints to query, False otherwise.
        """
        self.logger.debug("Querying next datapoint")

        if self.current_index >= len(self.datapoint_types):
            return False

        datapoint_type_code = self.datapoint_types[self.current_index]
        datapoint_type = DataPointType(datapoint_type_code)

        self.logger.debug(f"Datapoint: {datapoint_type}")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(datapoint_type.value),
        )
        self.current_index += 1
        return True

    def timeout(self) -> None:
        """Handle timeout event by querying next datapoint."""
        self.logger.debug("Timeout, querying next datapoint")
        query_next_datapoint = self.next_datapoint()
        if not query_next_datapoint:
            self.logger.debug("Received all datapoints telegram")
            self.service_response.success = True
            self.service_response.timestamp = datetime.now()
            self.service_response.serial_number = self.serial_number
            self.service_response.system_function = SystemFunction.READ_DATAPOINT

            # Emit finish signal
            self.on_finish.emit(self.service_response)

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

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
        ):
            self.logger.debug("Not a reply for our datapoint type")
            return

        self.logger.debug("Received a datapoint telegram")
        self.on_progress.emit(datapoint_telegram)

    def failed(self, message: str) -> None:
        """
        Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message

        # Emit finish signal
        self.on_finish.emit(self.service_response)

    def query_all_datapoints(
        self,
        serial_number: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Query all datapoints from a module.

        Args:
            serial_number: 10-digit module serial number.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting query_all_datapoints")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.serial_number = serial_number

    def set_timeout(self, timeout_seconds: float) -> None:
        """
        Set operation timeout.

        Args:
            timeout_seconds: Timeout in seconds.
        """
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.start_reactor()

    def stop_reactor(self) -> None:
        """Stop the reactor."""
        self.conbus_protocol.stop_reactor()

    def __enter__(self) -> "ConbusDatapointQueryAllService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.service_response = ConbusDatapointResponse(
            success=False,
            serial_number="",
        )
        self.datapoint_types = list(DataPointType)
        self.current_index = 0
        self.serial_number = ""
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager - cleanup signals and reactor."""
        # Disconnect protocol signals
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        # Disconnect service signals
        self.on_progress.disconnect()
        # Stop reactor
        self.stop_reactor()
