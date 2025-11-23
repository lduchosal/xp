"""Service for downloading ActionTable via Conbus protocol."""

import logging
from dataclasses import asdict
from typing import Any, Optional, Dict, Tuple

from psygnal import Signal

from xp.models.actiontable.actiontable import ActionTable
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class ActionTableService:
    """TCP client service for downloading action tables from Conbus modules.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses for action table downloads.

    Attributes:
        on_progress: Signal emitted with telegram frame when progress is made.
        on_error: Signal emitted with error message string when an error occurs.
        on_finish: Signal emitted with (ActionTable, Dict[str, Any], list[str]) when complete.
    """

    on_progress: Signal = Signal(str)
    on_error: Signal = Signal(str)
    on_finish: Signal = Signal(ActionTable, Dict[str, Any], list[str])  # (ActionTable, Dict[str, Any], list[str])

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        actiontable_serializer: ActionTableSerializer,
        telegram_service: TelegramService,
    ) -> None:
        """Initialize the action table download service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
            actiontable_serializer: Action table serializer.
            telegram_service: Telegram service for parsing.
        """
        self.conbus_protocol = conbus_protocol
        self.serializer = actiontable_serializer
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.actiontable_data: list[str] = []
        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            "Connection established, sending download actiontable telegram"
        )
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.DOWNLOAD_ACTIONTABLE,
            data_value="00",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.logger.debug(f"Telegram sent: {telegram_sent}")

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if (
            not telegram_received.checksum_valid
            or telegram_received.telegram_type != TelegramType.REPLY.value
            or telegram_received.serial_number != self.serial_number
        ):
            self.logger.debug("Not a reply response")
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )
        if reply_telegram.system_function not in (
            SystemFunction.ACTIONTABLE,
            SystemFunction.EOF,
        ):
            self.logger.debug("Not a actiontable response")
            return

        if reply_telegram.system_function == SystemFunction.ACTIONTABLE:
            self.logger.debug("Saving actiontable response")
            data_part = reply_telegram.data_value[2:]
            self.actiontable_data.append(data_part)
            self.on_progress.emit(".")

            self.conbus_protocol.send_telegram(
                telegram_type=TelegramType.SYSTEM,
                serial_number=self.serial_number,
                system_function=SystemFunction.ACK,
                data_value="00",
            )
            return

        if reply_telegram.system_function == SystemFunction.EOF:
            all_data = "".join(self.actiontable_data)
            # Deserialize from received data
            actiontable = self.serializer.from_encoded_string(all_data)
            actiontable_dict = asdict(actiontable)
            actiontable_short = self.serializer.format_decoded_output(actiontable)
            self.on_finish.emit(actiontable, actiontable_dict, actiontable_short)

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Timeout occurred")
        self.failed("Timeout")

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.on_error.emit(message)

    def start(
        self,
        serial_number: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            serial_number: Module serial number.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting actiontable")
        self.serial_number = serial_number
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        # Caller invokes start_reactor()

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

    def __enter__(self) -> "ActionTableService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.actiontable_data = []
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        # Disconnect protocol signals
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        # Disconnect service signals
        self.on_progress.disconnect()
        self.on_error.disconnect()
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
