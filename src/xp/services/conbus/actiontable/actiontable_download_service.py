"""Service for downloading ActionTable via Conbus protocol."""

import logging
from dataclasses import asdict
from enum import Enum
from typing import Any, Optional

from psygnal import SignalInstance
from statemachine import State, StateMachine

from xp.models.actiontable.actiontable import ActionTable
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService

# Constants
NO_ERROR_CODE = "00"
CHUNK_HEADER_LENGTH = 2  # data_value format: 2-char counter + actiontable chunk
MAX_ERROR_RETRIES = 3  # Max retries for error_status_received before giving up


class Phase(Enum):
    """Download workflow phases.

    The download workflow consists of three sequential phases:
    - INIT: Drain pending telegrams, query error status → proceed to DOWNLOAD
    - DOWNLOAD: Request actiontable, receive chunks with ACK, until EOF
    - CLEANUP: Drain pending telegrams, query error status → proceed to COMPLETED
    """

    INIT = "init"
    DOWNLOAD = "download"
    CLEANUP = "cleanup"


class ActionTableDownloadService(StateMachine):
    """Service for downloading action tables from Conbus modules via TCP.

    Inherits from StateMachine - the service IS the state machine. Uses guard
    conditions to share states between INIT and CLEANUP phases.
    see: Download-ActionTable-Workflow.dot

    States (9 total):
        idle -> receiving -> resetting -> waiting_ok -> requesting
             -> waiting_data <-> receiving_chunk -> processing_eof -> completed

    Phases - INIT and CLEANUP share the same states (receiving, resetting, waiting_ok):

    INIT phase (drain → reset → wait_ok):
        idle -> receiving -> resetting -> waiting_ok --(guard: is_init_phase)--> requesting

    DOWNLOAD phase (request → receive chunks → EOF):
        requesting -> waiting_data <-> receiving_chunk -> processing_eof

    CLEANUP phase (drain → reset → wait_ok):
        processing_eof -> receiving -> resetting -> waiting_ok --(guard: is_cleanup_phase)--> completed

    The drain/reset/wait_ok cycle:
    1. Drain pending telegrams (receiving state discards telegram without reading them).
       There may be a lot of telegram. We are listening and receiving until no more
       telegram arrive and timeout occurs.
    2. Timeout triggers error status query (resetting)
    3. Wait for response (waiting_ok)
    4. On no error: guard determines target (requesting or completed)
       On error: retry from drain step

    Attributes:
        on_progress: Signal emitted with "." for each chunk received.
        on_error: Signal emitted with error message string.
        on_actiontable_received: Signal emitted with (ActionTable, dict, list).
        on_finish: Signal emitted when download and cleanup completed.

    Example:
        >>> with download_service as service:
        ...     service.configure(serial_number="12345678")
        ...     service.on_actiontable_received.connect(handle_result)
        ...     service.start_reactor()
    """

    # States - unified for INIT and CLEANUP phases using guards
    idle = State(initial=True)
    receiving = State()  # Drain telegrams (INIT or CLEANUP phase)
    resetting = State()  # Query error status
    waiting_ok = State()  # Await error status response

    requesting = State()  # DOWNLOAD phase: send download request
    waiting_data = State()  # DOWNLOAD phase: await chunks
    receiving_chunk = State()  # DOWNLOAD phase: process chunk
    processing_eof = State()  # DOWNLOAD phase: deserialize result

    completed = State(final=True)

    # Phase transitions - shared states with guards for phase-dependent routing
    do_connect = idle.to(receiving)
    filter_telegram = receiving.to(receiving)  # Self-transition: drain to /dev/null
    do_timeout = receiving.to(resetting) | waiting_ok.to(receiving)
    send_error_status = resetting.to(waiting_ok)
    error_status_received = (
        waiting_ok.to(receiving, cond="can_retry")  # Retry if under limit
    )

    # Conditional transitions based on phase
    no_error_status_received = (
        waiting_ok.to(requesting, cond="is_init_phase")
        | waiting_ok.to(completed, cond="is_cleanup_phase")
    )

    # DOWNLOAD phase transitions
    send_download = requesting.to(waiting_data)
    receive_chunk = waiting_data.to(receiving_chunk)
    send_ack = receiving_chunk.to(waiting_data)
    receive_eof = waiting_data.to(processing_eof)

    # Return to drain/reset cycle for CLEANUP phase
    do_finish = processing_eof.to(receiving)

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
        self.logger = logging.getLogger(__name__)
        self._phase: Phase = Phase.INIT
        self._error_retry_count: int = 0
        self._signals_connected: bool = False

        # Signals (instance attributes to avoid conflict with statemachine)
        self.on_progress: SignalInstance = SignalInstance((str,))
        self.on_error: SignalInstance = SignalInstance((str,))
        self.on_finish: SignalInstance = SignalInstance()
        self.on_actiontable_received: SignalInstance = SignalInstance(
            (ActionTable, dict[str, Any], list[str])
        )

        # Initialize state machine first (before connecting signals)
        super().__init__(allow_event_without_transition=True)

        # Connect protocol signals
        self._connect_signals()

    # Guard conditions for phase-dependent transitions

    def is_init_phase(self) -> bool:
        """Guard: check if currently in INIT phase."""
        return self._phase == Phase.INIT

    def is_cleanup_phase(self) -> bool:
        """Guard: check if currently in CLEANUP phase."""
        return self._phase == Phase.CLEANUP

    def can_retry(self) -> bool:
        """Guard: check if retry is allowed (under max limit)."""
        return self._error_retry_count < MAX_ERROR_RETRIES

    # State machine lifecycle hooks
    # Note: receiving state is used to drain pending telegrams from the connection
    # pipe. Any telegram received in this state is intentionally discarded (sent
    # to /dev/null) to ensure a clean state before processing.

    def on_enter_receiving(self) -> None:
        """Enter receiving state - drain pending telegrams."""
        self.logger.debug(f"Entering RECEIVING state (phase={self._phase.value})")
        self.conbus_protocol.wait()

    def on_enter_resetting(self) -> None:
        """Enter resetting state - query error status."""
        self.logger.debug(f"Entering RESETTING state (phase={self._phase.value})")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_ERROR_CODE.value,
        )
        self.send_error_status()

    def on_enter_waiting_ok(self) -> None:
        """Enter waiting_ok state - awaiting error status response."""
        self.logger.debug(f"Entering WAITING_OK state (phase={self._phase.value})")
        self.conbus_protocol.wait()

    def on_enter_requesting(self) -> None:
        """Enter requesting state - send download request."""
        self._phase = Phase.DOWNLOAD
        self.logger.debug("Entering REQUESTING state - sending download request")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.DOWNLOAD_ACTIONTABLE,
            data_value=NO_ERROR_CODE,
        )
        self.send_download()

    def on_enter_waiting_data(self) -> None:
        """Enter waiting_data state - wait for actiontable chunks."""
        self.logger.debug("Entering WAITING_DATA state - awaiting chunks")
        self.conbus_protocol.wait()

    def on_enter_receiving_chunk(self) -> None:
        """Enter receiving_chunk state - send ACK."""
        self.logger.debug("Entering RECEIVING_CHUNK state - sending ACK")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.ACK,
            data_value=NO_ERROR_CODE,
        )
        self.send_ack()

    def on_enter_processing_eof(self) -> None:
        """Enter processing_eof state - deserialize and emit result, then cleanup."""
        self.logger.debug("Entering PROCESSING_EOF state - deserializing")
        all_data = "".join(self.actiontable_data)
        actiontable = self.serializer.from_encoded_string(all_data)
        actiontable_dict = asdict(actiontable)
        actiontable_short = self.serializer.format_decoded_output(actiontable)
        self.on_actiontable_received.emit(
            actiontable, actiontable_dict, actiontable_short
        )
        # Switch to CLEANUP phase before returning to receiving state
        self._phase = Phase.CLEANUP
        self.do_finish()

    def on_enter_completed(self) -> None:
        """Enter completed state - download finished."""
        self.logger.debug("Entering COMPLETED state - download finished")
        self.on_finish.emit()

    # Protocol event handlers

    def _on_connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection made")
        if self.idle.is_active:
            self.do_connect()

    def _on_telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.logger.debug(f"Telegram sent: {telegram_sent}")

    def _on_read_datapoint_received(self, reply_telegram: ReplyTelegram) -> None:
        """Handle READ_DATAPOINT response for error status check.

        Args:
            reply_telegram: The parsed reply telegram.
        """
        self.logger.debug(f"Received READ_DATAPOINT in {self.current_state}")

        if reply_telegram.datapoint_type != DataPointType.MODULE_ERROR_CODE:
            self.logger.debug(
                f"Filtered: not a MODULE_ERROR_CODE (got {reply_telegram.datapoint_type})"
            )
            return

        if not self.waiting_ok.is_active:
            return

        is_no_error = reply_telegram.data_value == NO_ERROR_CODE
        if is_no_error:
            self._error_retry_count = 0  # Reset on success
            self.no_error_status_received()  # Guards determine target state
        else:
            self._error_retry_count += 1
            self.logger.debug(
                f"Error status received, retry {self._error_retry_count}/{MAX_ERROR_RETRIES}"
            )
            # Guard can_retry blocks transition if max retries exceeded
            self.error_status_received()
            # Check if guard blocked the transition (still in waiting_ok)
            if self.waiting_ok.is_active:
                self.logger.error(
                    f"Max error retries ({MAX_ERROR_RETRIES}) exceeded, giving up"
                )
                self.on_error.emit(
                    f"Module error persists after {MAX_ERROR_RETRIES} retries"
                )

    def _on_actiontable_chunk_received(self, reply_telegram: ReplyTelegram) -> None:
        """Handle actiontable chunk telegram received.

        Args:
            reply_telegram: The parsed reply telegram containing chunk data.
        """
        self.logger.debug(f"Received actiontable chunk in {self.current_state}")
        if self.waiting_data.is_active:
            data_part = reply_telegram.data_value[CHUNK_HEADER_LENGTH:]
            self.actiontable_data.append(data_part)
            self.on_progress.emit(".")
            self.receive_chunk()

    def _on_eof_received(self, _reply_telegram: ReplyTelegram) -> None:
        """Handle EOF telegram received.

        Args:
            _reply_telegram: The parsed reply telegram (unused).
        """
        self.logger.debug(f"Received EOF in {self.current_state}")
        if self.waiting_data.is_active:
            self.receive_eof()

    def _on_telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Received {telegram_received} in {self.current_state}")

        # In receiving state, drain pending telegrams from pipe (discard to /dev/null).
        # This ensures clean state before processing by clearing any stale messages.
        if self.receiving.is_active:
            self.filter_telegram()
            return

        # Filter invalid telegrams
        if not telegram_received.checksum_valid:
            self.logger.debug("Filtered: invalid checksum")
            return

        if telegram_received.telegram_type != TelegramType.REPLY.value:
            self.logger.debug(
                f"Filtered: not a reply (got {telegram_received.telegram_type})"
            )
            return

        if telegram_received.serial_number != self.serial_number:
            self.logger.debug(
                f"Filtered: wrong serial {telegram_received.serial_number} != {self.serial_number}"
            )
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )

        if reply_telegram.system_function == SystemFunction.READ_DATAPOINT:
            self._on_read_datapoint_received(reply_telegram)
            return

        if reply_telegram.system_function == SystemFunction.ACTIONTABLE:
            self._on_actiontable_chunk_received(reply_telegram)
            return

        if reply_telegram.system_function == SystemFunction.EOF:
            self._on_eof_received(reply_telegram)
            return

    def _on_timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug(f"Timeout occurred (phase={self._phase.value})")
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
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.on_error.emit(message)

    # Public API

    def configure(
        self,
        serial_number: str,
        timeout_seconds: Optional[float] = 2.0,
    ) -> None:
        """Configure download parameters before starting.

        Sets the target module serial number and timeout. Call this before
        start_reactor() to configure the download target.

        Args:
            serial_number: Module serial number to download from.
            timeout_seconds: Timeout in seconds for each operation (default 2.0).

        Raises:
            RuntimeError: If called while download is in progress.
        """
        if not self.idle.is_active:
            raise RuntimeError("Cannot configure while download in progress")
        self.logger.info("Configuring actiontable download")
        self.serial_number = serial_number
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds

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

    def _connect_signals(self) -> None:
        """Connect protocol signals to handlers (idempotent)."""
        if self._signals_connected:
            return
        self.conbus_protocol.on_connection_made.connect(self._on_connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self._on_telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self._on_telegram_received)
        self.conbus_protocol.on_timeout.connect(self._on_timeout)
        self.conbus_protocol.on_failed.connect(self._on_failed)
        self._signals_connected = True

    def _disconnect_signals(self) -> None:
        """Disconnect protocol signals from handlers (idempotent)."""
        if not self._signals_connected:
            return
        self.conbus_protocol.on_connection_made.disconnect(self._on_connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self._on_telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self._on_telegram_received)
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
        self._phase = Phase.INIT
        self._error_retry_count = 0
        # Reset state machine to idle
        self._reset_state()
        # Reconnect signals (in case previously disconnected)
        self._connect_signals()
        return self

    def _reset_state(self) -> None:
        """Reset state machine to initial state."""
        # python-statemachine uses model.state to track current state
        # Set it directly to the initial state id
        self.model.state = self.idle.id

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
