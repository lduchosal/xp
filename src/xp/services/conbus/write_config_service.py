"""
Conbus Link Number Service for setting module link numbers.

This service handles setting link numbers for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from psygnal import Signal

from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class WriteConfigService:
    """
    Service for writing module settings via Conbus telegrams.

    Handles setting assignment by sending F04DXX telegrams and processing
    ACK/NAK responses from modules.

    Attributes:
        conbus_protocol: Protocol for Conbus communication.
        telegram_service: Service for parsing telegrams.
        on_finish: Signal emitted when write operation completes (with response).
    """

    on_finish: Signal = Signal(ConbusWriteConfigResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_service: TelegramService,
    ) -> None:
        """
        Initialize the Conbus link number set service.

        Args:
            conbus_protocol: Protocol for Conbus communication.
            telegram_service: Service for parsing telegrams.
        """
        self.conbus_protocol = conbus_protocol
        self.telegram_service = telegram_service
        self.datapoint_type: Optional[DataPointType] = None
        self.serial_number: str = ""
        self.data_value: str = ""
        self.write_config_response: ConbusWriteConfigResponse = (
            ConbusWriteConfigResponse(
                success=False,
                serial_number=self.serial_number,
            )
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection made event."""
        self.logger.debug(f"Connection established, writing config {self.data_value}.")

        # Validate parameters before sending
        if not self.serial_number or len(self.serial_number) != 10:
            self.failed(f"Serial number must be 10 digits, got: {self.serial_number}")
            return

        if len(self.data_value) < 2:
            self.failed(f"data_value must be at least 2 bytes, got: {self.data_value}")
            return

        if not self.datapoint_type:
            self.failed(f"datapoint_type must be defined, got: {self.datapoint_type}")
            return

        # Send WRITE_CONFIG telegram
        # Function F04 = WRITE_CONFIG,
        # Datapoint = D datapoint_type
        # Data = XX
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.WRITE_CONFIG,
            data_value=f"{self.datapoint_type.value}{self.data_value}",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.write_config_response.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")

        if not self.write_config_response.received_telegrams:
            self.write_config_response.received_telegrams = []
        self.write_config_response.received_telegrams.append(telegram_received.frame)

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

        if not reply_telegram or reply_telegram.system_function not in (
            SystemFunction.ACK,
            SystemFunction.NAK,
        ):
            self.logger.debug("Not a write config reply")
            return

        succeed = (
            True if reply_telegram.system_function == SystemFunction.ACK else False
        )
        self.finished(
            succeed_or_failed=succeed, system_function=reply_telegram.system_function
        )

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Timeout occurred")
        self.finished(succeed_or_failed=False, message="Timeout")

    def failed(self, message: str) -> None:
        """
        Handle telegram failed event.

        Args:
            message: The error message.
        """
        self.logger.debug("Failed to send telegram")
        self.finished(succeed_or_failed=False, message=message)

    def finished(
        self,
        succeed_or_failed: bool,
        message: Optional[str] = None,
        system_function: Optional[SystemFunction] = None,
    ) -> None:
        """
        Handle successful link number set operation.

        Args:
            succeed_or_failed: succeed true, failed false.
            message: error message if any.
            system_function: The system function from the reply telegram.
        """
        self.logger.debug("finished writing config")
        self.write_config_response.success = succeed_or_failed
        self.write_config_response.error = message
        self.write_config_response.timestamp = datetime.now()
        self.write_config_response.serial_number = self.serial_number
        self.write_config_response.system_function = system_function
        self.write_config_response.datapoint_type = self.datapoint_type
        self.write_config_response.data_value = self.data_value

        # Emit finish signal
        self.on_finish.emit(self.write_config_response)

    def write_config(
        self,
        serial_number: str,
        datapoint_type: DataPointType,
        data_value: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Write config to a specific module.

        Args:
            serial_number: 10-digit module serial number.
            datapoint_type: the datapoint type to write to.
            data_value: the data to write.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting write_config")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.datapoint_type = datapoint_type
        self.data_value = data_value

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

    def __enter__(self) -> "WriteConfigService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        self.write_config_response = ConbusWriteConfigResponse(
            success=False, serial_number=""
        )
        self.datapoint_type = None
        self.serial_number = ""
        self.data_value = ""
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
