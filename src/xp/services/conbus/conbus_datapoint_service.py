"""
Conbus Datapoint Service for querying module datapoints.

This service handles datapoint query operations for modules through Conbus telegrams.
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
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusDatapointService:
    """
    Service for querying datapoints from Conbus modules.

    Uses ConbusEventProtocol to provide datapoint query functionality
    for reading sensor data and module information.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        telegram_service: Service for parsing telegrams.
        on_finish: Signal emitted when datapoint query completes (with response).
    """

    on_finish: Signal = Signal(ConbusDatapointResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_service: TelegramService,
    ) -> None:
        """
        Initialize the Conbus datapoint service.

        Args:
            conbus_protocol: Protocol instance for Conbus communication.
            telegram_service: Service for parsing telegrams.
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
        self.datapoint_type: Optional[DataPointType] = None
        self.service_response: ConbusDatapointResponse = ConbusDatapointResponse(
            success=False,
            serial_number=self.serial_number,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            f"Connection established, querying datapoint {self.datapoint_type}."
        )
        if self.datapoint_type is None:
            self.failed("Datapoint type not set")
            return

        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(self.datapoint_type.value),
        )

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
            or datapoint_telegram.datapoint_type != self.datapoint_type
        ):
            self.logger.debug("Not a reply for our datapoint type")
            return

        self.logger.debug("Received datapoint telegram")
        self.succeed(datapoint_telegram)

    def succeed(self, datapoint_telegram: ReplyTelegram) -> None:
        """
        Handle successful datapoint query.

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

        # Emit finish signal
        self.on_finish.emit(self.service_response)
        self.stop_reactor()

    def timeout(self) -> None:
        """Handle timeout event."""
        self.failed("Timeout")

    def failed(self, message: str) -> None:
        """
        Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.error = message

        # Emit finish signal
        self.on_finish.emit(self.service_response)

    def query_datapoint(
        self,
        serial_number: str,
        datapoint_type: DataPointType,
        timeout_seconds: float = 1.0,
    ) -> None:
        """
        Query a specific datapoint from a module.

        Args:
            serial_number: 10-digit module serial number.
            datapoint_type: Type of datapoint to query.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting query_datapoint")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.datapoint_type = datapoint_type

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

    def __enter__(self) -> "ConbusDatapointService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        self.datapoint_response = ConbusDatapointResponse(success=False)
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        self.on_finish.disconnect()
        self.stop_reactor()
