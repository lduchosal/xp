"""Service for downloading ActionTable via Conbus protocol."""

import logging
from typing import Any, Optional

from psygnal import Signal

from xp.models.actiontable.actiontable_type import ActionTableType
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.actiontable.download_state_machine import (
    MAX_ERROR_RETRIES,
    DownloadStateMachine,
)
from xp.services.actiontable.msactiontable_xp20_serializer import (
    Xp20MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp33_serializer import (
    Xp33MsActionTableSerializer,
)
from xp.services.actiontable.serializer_protocol import ActionTableSerializerProtocol
from xp.services.protocol.conbus_event_protocol import (
    NO_ERROR_CODE,
    ConbusEventProtocol,
)


class ActionTableDownloadService(DownloadStateMachine):
    """
    Service for downloading action tables from Conbus modules via TCP.

    Inherits from ActionTableDownloadStateMachine and overrides on_enter_*
    methods to add protocol-specific behavior.

    The workflow consists of three phases:

    INIT phase (drain → reset → wait_ok):
        Connection established, drain pending telegrams, query error status.

    DOWNLOAD phase (request → receive chunks → EOF):
        Request actiontable, receive and ACK chunks until EOF.

    CLEANUP phase (drain → reset → wait_ok):
        After EOF, drain remaining telegrams and verify final status.

    Attributes:
        on_progress: Signal emitted with "." for each chunk received.
        on_error: Signal emitted with error message string.
        on_actiontable_received: Signal emitted with (ActionTable, list).
        on_finish: Signal emitted when download and cleanup completed.

    Example:
        >>> with download_service as service:
        ...     service.configure(serial_number="12345678")
        ...     service.on_actiontable_received.connect(handle_result)
        ...     service.start_reactor()
    """

    # Service signals
    on_progress: Signal = Signal(str)
    on_error: Signal = Signal(str)
    on_finish: Signal = Signal()
    on_actiontable_received: Signal = Signal(Any, list[str])

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        actiontable_serializer: ActionTableSerializer,
        msactiontable_serializer_xp20: Xp20MsActionTableSerializer,
        msactiontable_serializer_xp24: Xp24MsActionTableSerializer,
        msactiontable_serializer_xp33: Xp33MsActionTableSerializer,
    ) -> None:
        """
        Initialize the action table download service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
            actiontable_serializer: Action table serializer.
            msactiontable_serializer_xp20: XP20 master station action table serializer.
            msactiontable_serializer_xp24: XP24 master station action table serializer.
            msactiontable_serializer_xp33: XP33 master station action table serializer.
        """
        self.conbus_protocol = conbus_protocol
        self.actiontable_serializer = actiontable_serializer
        self.msactiontable_serializer_xp20 = msactiontable_serializer_xp20
        self.msactiontable_serializer_xp24 = msactiontable_serializer_xp24
        self.msactiontable_serializer_xp33 = msactiontable_serializer_xp33
        self.serializer: ActionTableSerializerProtocol = actiontable_serializer

        self.serial_number: str = ""
        self.actiontable_data: list[str] = []
        self._signals_connected: bool = False

        # Initialize state machine (must be last - triggers introspection)
        super().__init__()

        # Override logger for service-specific logging
        self.logger = logging.getLogger(__name__)

        # Connect protocol signals
        self._connect_signals()

    # Override state entry hooks with protocol behavior

    def on_enter_receiving(self) -> None:
        """Enter receiving state - wait for telegrams to drain."""
        self.logger.debug(f"Entering RECEIVING state (phase={self.phase.value})")
        self.conbus_protocol.wait()

    def on_enter_resetting(self) -> None:
        """Enter resetting state - send error status query."""
        self.logger.debug(f"Entering RESETTING state (phase={self.phase.value})")
        self.conbus_protocol.send_error_status_query(serial_number=self.serial_number)
        self.send_error_status()

    def on_enter_waiting_ok(self) -> None:
        """Enter waiting_ok state - wait for error status response."""
        self.logger.debug(f"Entering WAITING_OK state (phase={self.phase.value})")
        self.conbus_protocol.wait()

    def on_enter_requesting(self) -> None:
        """Enter requesting state - send download request."""
        self.enter_download_phase()  # Sets phase to DOWNLOAD
        self.conbus_protocol.send_download_request(
            serial_number=self.serial_number,
            actiontable_type=self.serializer.download_type(),
        )
        self.send_download()

    def on_enter_waiting_data(self) -> None:
        """Enter waiting_data state - wait for actiontable chunks."""
        self.logger.debug("Entering WAITING_DATA state - awaiting chunks")
        self.conbus_protocol.wait()

    def on_enter_receiving_chunk(self) -> None:
        """Enter receiving_chunk state - send ACK."""
        self.logger.debug("Entering RECEIVING_CHUNK state - sending ACK")
        self.conbus_protocol.send_ack(serial_number=self.serial_number)
        self.send_ack()

    def on_enter_processing_eof(self) -> None:
        """Enter processing_eof state - deserialize and emit result."""
        self.logger.debug("Entering PROCESSING_EOF state - deserializing")
        all_data = "".join(self.actiontable_data)
        actiontable = self.serializer.from_encoded_string(all_data)
        actiontable_short = self.serializer.to_short_string(actiontable)
        self.on_actiontable_received.emit(actiontable, actiontable_short)
        # Switch to CLEANUP phase
        self.start_cleanup_phase()

    def on_enter_completed(self) -> None:
        """Enter completed state - emit finish signal."""
        self.logger.debug("Entering COMPLETED state - download finished")
        self.on_finish.emit()

    def on_max_retries_exceeded(self) -> None:
        """Handle max retries exceeded - emit error signal."""
        self.logger.error(f"Max error retries ({MAX_ERROR_RETRIES}) exceeded")
        self.on_error.emit(f"Module error persists after {MAX_ERROR_RETRIES} retries")

    # Protocol event handlers

    def _on_connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection made")
        if self.idle.is_active:
            self.do_connect()

    def _on_read_datapoint_received(self, reply_telegram: ReplyTelegram) -> None:
        """
        Handle READ_DATAPOINT response for error status check.

        Args:
            reply_telegram: The parsed reply telegram.
        """
        self.logger.debug(f"Received READ_DATAPOINT in {self.current_state}")
        if reply_telegram.serial_number != self.serial_number:
            return

        if reply_telegram.datapoint_type != DataPointType.MODULE_ERROR_CODE:
            return

        if not self.waiting_ok.is_active:
            return

        is_no_error = reply_telegram.data_value == NO_ERROR_CODE
        if is_no_error:
            self.handle_no_error_received()
        else:
            self.handle_error_received()

    def _on_actiontable_chunk_received(
        self, reply_telegram: ReplyTelegram, actiontable_chunk: str
    ) -> None:
        """
        Handle actiontable chunk telegram received.

        Args:
            reply_telegram: The parsed reply telegram containing chunk data.
            actiontable_chunk: The chunk data.
        """
        self.logger.debug(f"Received actiontable chunk in {self.current_state}")
        if reply_telegram.serial_number != self.serial_number:
            return

        if self.waiting_data.is_active:
            self.actiontable_data.append(actiontable_chunk)
            self.on_progress.emit(".")
            self.receive_chunk()

    def _on_eof_received(self, reply_telegram: ReplyTelegram) -> None:
        """
        Handle EOF telegram received.

        Args:
            reply_telegram: The parsed reply telegram (unused).
        """
        self.logger.debug(f"Received EOF in {self.current_state}")
        if reply_telegram.serial_number != self.serial_number:
            return

        if self.waiting_data.is_active:
            self.receive_eof()

    def _on_telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Received {telegram_received} in {self.current_state}")

        # In receiving state, drain pending telegrams from pipe (discard to /dev/null).
        # This ensures clean state before processing by clearing any stale messages.
        if self.receiving.is_active:
            self.filter_telegram()
            return

    def _on_timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug(f"Timeout occurred (phase={self.phase.value})")
        if self.receiving.is_active:
            self.do_timeout()  # receiving -> resetting
        elif self.waiting_ok.is_active:
            self.do_timeout()  # waiting_ok -> receiving (retry)
        elif self.waiting_data.is_active:
            self.logger.error("Timeout waiting for actiontable data")
            self.on_error.emit("Timeout waiting for actiontable data")
        else:
            self.logger.debug("Timeout in non-recoverable state")
            self.on_error.emit("Timeout")

    def _on_failed(self, message: str) -> None:
        """
        Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.on_error.emit(message)

    # Public API

    def configure(
        self,
        serial_number: str,
        actiontable_type: ActionTableType,
        timeout_seconds: Optional[float] = 2.0,
    ) -> None:
        """
        Configure download parameters before starting.

        Sets the target module serial number and timeout. Call this before
        start_reactor() to configure the download target.

        Args:
            serial_number: Module serial number to download from.
            actiontable_type: Type of action table to download.
            timeout_seconds: Timeout in seconds for each operation (default 2.0).

        Raises:
            RuntimeError: If called while download is in progress.
        """
        if not self.idle.is_active:
            raise RuntimeError("Cannot configure while download in progress")
        self.logger.info("Configuring actiontable download")
        self.serial_number = serial_number
        self.actiontable_data = []

        if actiontable_type == ActionTableType.ACTIONTABLE:
            self.serializer = self.actiontable_serializer
        elif actiontable_type == ActionTableType.MSACTIONTABLE_XP20:
            self.serializer = self.msactiontable_serializer_xp20
        elif actiontable_type == ActionTableType.MSACTIONTABLE_XP24:
            self.serializer = self.msactiontable_serializer_xp24
        elif actiontable_type == ActionTableType.MSACTIONTABLE_XP33:
            self.serializer = self.msactiontable_serializer_xp33
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds

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

    def _connect_signals(self) -> None:
        """Connect protocol signals to handlers (idempotent)."""
        if self._signals_connected:
            return
        self.conbus_protocol.on_connection_made.connect(self._on_connection_made)
        self.conbus_protocol.on_telegram_received.connect(self._on_telegram_received)
        self.conbus_protocol.on_read_datapoint_received.connect(
            self._on_read_datapoint_received
        )
        self.conbus_protocol.on_actiontable_chunk_received.connect(
            self._on_actiontable_chunk_received
        )
        self.conbus_protocol.on_eof_received.connect(self._on_eof_received)
        self.conbus_protocol.on_timeout.connect(self._on_timeout)
        self.conbus_protocol.on_failed.connect(self._on_failed)
        self._signals_connected = True

    def _disconnect_signals(self) -> None:
        """Disconnect protocol signals from handlers (idempotent)."""
        if not self._signals_connected:
            return
        self.conbus_protocol.on_connection_made.disconnect(self._on_connection_made)
        self.conbus_protocol.on_telegram_received.disconnect(self._on_telegram_received)
        self.conbus_protocol.on_read_datapoint_received.disconnect(
            self._on_read_datapoint_received
        )
        self.conbus_protocol.on_actiontable_chunk_received.disconnect(
            self._on_actiontable_chunk_received
        )
        self.conbus_protocol.on_eof_received.disconnect(self._on_eof_received)
        self.conbus_protocol.on_timeout.disconnect(self._on_timeout)
        self.conbus_protocol.on_failed.disconnect(self._on_failed)
        self._signals_connected = False

    def __enter__(self) -> "ActionTableDownloadService":
        """Enter context manager - reset state and reconnect signals.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.actiontable_data = []
        # Reset state machine
        self.reset()
        # Reconnect signals (in case previously disconnected)
        self._connect_signals()
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        self._disconnect_signals()
        # Disconnect service signals
        self.on_progress.disconnect()
        self.on_error.disconnect()
        self.on_actiontable_received.disconnect()
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
