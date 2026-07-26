# Copyright (c) 2025 ldvchosal
"""Conbus Output Service for sending action telegrams to Conbus modules.

This service handles sending action telegrams (ON/OFF) to module outputs and processing
ACK/NAK responses.
"""

import logging
from types import TracebackType
from typing import Self

from psygnal import Signal

from xp.models.conbus.conbus_output import ConbusOutputResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.action_type import ActionType
from xp.models.telegram.output_telegram import OutputTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_output_service import (
    TelegramOutputService,
    XPOutputError,
)
from xp.utils.time_utils import local_now


class ConbusOutputError(Exception):
    """Raised when Conbus output operations fail."""


class ConbusOutputService:
    """Service for sending action telegrams to Conbus module outputs.

    Manages action telegram transmission (ON/OFF) and processes
    ACK/NAK responses from modules.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        on_finish: Signal emitted when operation finishes (with result).

    """

    conbus_protocol: ConbusEventProtocol
    on_finish: Signal = Signal(ConbusOutputResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_output_service: TelegramOutputService,
    ) -> None:
        """Initialize the Conbus output service.

        Args:
            conbus_protocol: ConbusEventProtocol for communication.
            telegram_output_service: TelegramOutputService for telegram
                generation/parsing.

        """
        self.conbus_protocol = conbus_protocol
        self.telegram_output_service = telegram_output_service

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        # Initialize state
        self.serial_number: str = ""
        self.output_number: int = 0
        self.action_type: ActionType = ActionType.ON_RELEASE
        self.output_state: str = ""
        self.service_response: ConbusOutputResponse = ConbusOutputResponse(
            success=False,
            serial_number=self.serial_number,
            output_number=self.output_number,
            action_type=self.action_type,
            timestamp=local_now(),
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            "Connection established, sending action %s to output %s.",
            self.action_type,
            self.output_number,
        )

        # Validate parameters before sending
        try:
            self.telegram_output_service.validate_output_number(self.output_number)
            self.telegram_output_service.validate_serial_number(self.serial_number)
        except XPOutputError as e:
            self.failed(str(e))
            return

        # Send F27D{output:02d}{action} telegram
        # F27 = ACTION, D = data with output number and action type
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.ACTION,
            data_value=f"{self.output_number:02d}{self.action_type.value}",
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
        self.logger.debug("Telegram received: %s", telegram_received)

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

        # Parse the reply telegram to get ACK/NAK
        output_telegram = self.telegram_output_service.parse_reply_telegram(
            telegram_received.frame
        )

        if output_telegram and output_telegram.system_function in {
            SystemFunction.ACK,
            SystemFunction.NAK,
        }:
            self.logger.debug("Received %s response", output_telegram.system_function)
            self.succeed(output_telegram)
        else:
            self.logger.debug(
                "Unexpected system function: %s", output_telegram.system_function
            )

    def succeed(self, output_telegram: OutputTelegram) -> None:
        """Handle successful output action.

        Args:
            output_telegram: The output telegram received as response.

        """
        self.logger.debug("Successfully sent action to output")
        self.service_response.success = True
        self.service_response.timestamp = local_now()
        self.service_response.serial_number = self.serial_number
        self.service_response.output_number = self.output_number
        self.service_response.action_type = self.action_type
        self.service_response.output_telegram = output_telegram
        self.on_finish.emit(self.service_response)

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Timeout occurred")
        self.failed("Timeout")

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.

        """
        self.logger.debug("Failed with message: %s", message)
        self.service_response.success = False
        self.service_response.timestamp = local_now()
        self.service_response.serial_number = self.serial_number
        self.service_response.output_number = self.output_number
        self.service_response.action_type = self.action_type
        self.service_response.error = message
        self.on_finish.emit(self.service_response)

    def send_action(
        self,
        serial_number: str,
        output_number: int,
        action_type: ActionType,
        timeout_seconds: float | None = None,
    ) -> None:
        """Send an action telegram to a module output.

        Args:
            serial_number: 10-digit module serial number.
            output_number: Output number (0-99).
            action_type: Action to perform (ON_RELEASE, OFF_PRESS, etc.).
            timeout_seconds: Optional timeout in seconds.

        """
        self.logger.info("Starting send_action")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.output_number = output_number
        self.action_type = action_type

    def set_timeout(self, timeout_seconds: float) -> None:
        """Set operation timeout.

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

    def __enter__(self) -> Self:
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.

        """
        # Reset state for singleton reuse
        self.service_response = ConbusOutputResponse(
            success=False,
            serial_number="",
            output_number=0,
            action_type=ActionType.ON_RELEASE,
            timestamp=local_now(),
        )
        self.output_state = ""
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and disconnect signals."""
        # Disconnect protocol signals
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        # Disconnect service signals
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
