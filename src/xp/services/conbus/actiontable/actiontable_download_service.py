"""Service for downloading ActionTable via Conbus protocol."""

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

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


class ActionTableDownloadService(StateMachine):
    """TCP client service for downloading action tables from Conbus modules.

    Inherits from StateMachine - the service IS the state machine.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses for action table downloads.

    Attributes:
        on_progress: Signal emitted with telegram frame when progress is made.
        on_error: Signal emitted with error message string when an error occurs.
        on_finish: Signal emitted with (ActionTable, Dict[str, Any], list[str]) when complete.
        idle: Initial state, waiting for connection.
        receiving: Listening for telegrams, filtering relevant responses.
        resetting: Timeout occurred, preparing error status query.
        waiting_ok: Sent error status query, awaiting ACK/NAK.
        requesting: Ready to send download request.
        waiting_data: Awaiting actiontable chunk or EOF.
        receiving_chunk: Processing received actiontable data.
        processing_eof: Received EOF, deserializing actiontable.
        completed: Download finished successfully.
        do_connect: Transition from idle to receiving.
        do_timeout: Transition from receiving to resetting.
        send_error_status: Transition from resetting to waiting_ok.
        error_status_received: Transition from waiting_ok to receiving (retry).
        no_error_status_received: Transition from waiting_ok to requesting or completed.
        send_download: Transition from requesting to waiting_data.
        receive_chunk: Transition from waiting_data to receiving_chunk.
        send_ack: Transition from receiving_chunk to waiting_data.
        receive_eof: Transition from waiting_data to processing_eof.
        do_finish: Transition from processing_eof to receiving.
        receiving2: Second receiving state after EOF processing.
        resetting2: Second resetting state for finalization phase.
        waiting_ok2: Second waiting_ok state for finalization phase.
        filter_telegram: Self-transition for filtering telegrams in receiving state.
        filter_telegram2: Self-transition for filtering telegrams in receiving2 state.
        do_timeout2: Timeout transition for finalization phase.
        send_error_status2: Error status query transition for finalization phase.
        error_status_received2: Error received transition for finalization phase.
        no_error_status_received2: No error received transition to completed state.
    """

    # States (9 states as per spec)
    idle = State(initial=True)
    receiving = State()
    resetting = State()
    waiting_ok = State()

    requesting = State()
    waiting_data = State()
    receiving_chunk = State()
    processing_eof = State()

    receiving2 = State()
    resetting2 = State()
    waiting_ok2 = State()

    completed = State(final=True)

    # Phase 1: Connection & Initialization
    do_connect = idle.to(receiving)
    filter_telegram = receiving.to(receiving)  # Self-transition for filtering
    do_timeout = receiving.to(resetting) | waiting_ok.to(receiving)
    send_error_status = resetting.to(waiting_ok)
    error_status_received = waiting_ok.to(receiving)
    no_error_status_received = waiting_ok.to(requesting)

    # Phase 2: Download
    send_download = requesting.to(waiting_data)
    receive_chunk = waiting_data.to(receiving_chunk)
    send_ack = receiving_chunk.to(waiting_data)
    receive_eof = waiting_data.to(processing_eof)

    # Phase 3: Finalization
    do_finish = processing_eof.to(receiving2)
    filter_telegram2 = receiving2.to(receiving2)  # Self-transition for filtering
    do_timeout2 = receiving2.to(resetting2) | waiting_ok2.to(receiving2)
    send_error_status2 = resetting2.to(waiting_ok2)
    error_status_received2 = waiting_ok2.to(receiving2)
    no_error_status_received2 = waiting_ok2.to(completed)

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

        # Signals (instance attributes to avoid conflict with statemachine)
        self.on_progress: SignalInstance = SignalInstance((str,))
        self.on_error: SignalInstance = SignalInstance((str,))
        self.on_finish: SignalInstance = SignalInstance()
        self.on_actiontable_received: SignalInstance = SignalInstance(
            (ActionTable, Dict[str, Any], list[str])
        )

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self._on_connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self._on_telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self._on_telegram_received)
        self.conbus_protocol.on_timeout.connect(self._on_timeout)
        self.conbus_protocol.on_failed.connect(self._on_failed)

        # Initialize state machine
        super().__init__(allow_event_without_transition=True)

    # State machine lifecycle hooks

    def on_enter_receiving(self) -> None:
        """Enter receiving state - listening for telegrams."""
        self.logger.debug("Entering RECEIVING state - waiting for telegrams")
        self.conbus_protocol.wait()

    def on_enter_receiving2(self) -> None:
        """Enter receiving state - listening for telegrams."""
        self.logger.debug("Entering RECEIVING2 state - waiting for telegrams")
        self.conbus_protocol.wait()

    def on_enter_resetting(self) -> None:
        """Enter resetting state - query error status."""
        self.logger.debug("Entering RESETTING state - querying error status")

        # query_datapoint_module_error_code
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_ERROR_CODE.value,
        )
        self.send_error_status()

    def on_enter_resetting2(self) -> None:
        """Enter resetting state - query error status."""
        self.logger.debug("Entering RESETTING2 state - querying error status")

        # query_datapoint_module_error_code
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_ERROR_CODE.value,
        )
        self.send_error_status2()

    def on_enter_waiting_ok(self) -> None:
        """Enter waiting_ok state - awaiting ERROR/NO_ERROR."""
        self.logger.debug("Entering WAITING_OK state - awaiting ERROR/NO_ERROR")
        self.conbus_protocol.wait()

    def on_enter_waiting_ok2(self) -> None:
        """Enter waiting_ok state - awaiting ERROR/NO_ERROR."""
        self.logger.debug("Entering WAITING_OK state - awaiting ERROR/NO_ERROR")
        self.conbus_protocol.wait()

    def on_enter_requesting(self) -> None:
        """Enter requesting state - send download request."""
        self.logger.debug("Entering REQUESTING state - sending download request")
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.DOWNLOAD_ACTIONTABLE,
            data_value="00",
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
            data_value="00",
        )
        self.send_ack()

    def on_enter_processing_eof(self) -> None:
        """Enter processing_eof state - deserialize and emit result."""
        self.logger.debug("Entering PROCESSING_EOF state - deserializing")
        all_data = "".join(self.actiontable_data)
        actiontable = self.serializer.from_encoded_string(all_data)
        actiontable_dict = asdict(actiontable)
        actiontable_short = self.serializer.format_decoded_output(actiontable)
        self.on_actiontable_received.emit(
            actiontable, actiontable_dict, actiontable_short
        )
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

        if reply_telegram.data_value == "00":
            if self.waiting_ok.is_active:
                self.no_error_status_received()

        if reply_telegram.data_value != "00":
            if self.waiting_ok.is_active:
                self.error_status_received()

        if reply_telegram.data_value == "00":
            if self.waiting_ok2.is_active:
                self.no_error_status_received2()

        if reply_telegram.data_value != "00":
            if self.waiting_ok2.is_active:
                self.error_status_received2()

    def _on_ack_received(self, _reply_telegram: ReplyTelegram) -> None:
        """Handle ACK telegram received.

        Args:
            _reply_telegram: The parsed reply telegram (unused).
        """
        self.logger.debug(f"Received ACK in {self.current_state}")
        if self.waiting_ok.is_active:
            self.ack_received()

        if self.waiting_ok2.is_active:
            self.ack_received2()

    def _on_nack_received(self, _reply_telegram: ReplyTelegram) -> None:
        """Handle NAK telegram received.

        Args:
            _reply_telegram: The parsed reply telegram (unused).
        """
        self.logger.debug(f"Received NAK in {self.current_state}")
        if self.waiting_ok.is_active:
            self.nak_received()

    def _on_actiontable_chunk_received(self, reply_telegram: ReplyTelegram) -> None:
        """Handle actiontable chunk telegram received.

        Args:
            reply_telegram: The parsed reply telegram containing chunk data.
        """
        self.logger.debug(f"Received actiontable chunk in {self.current_state}")
        if self.waiting_data.is_active:
            data_part = reply_telegram.data_value[2:]
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
        self.logger.debug(f"Received{telegram_received} in {self.current_state}")
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

        if reply_telegram.system_function == SystemFunction.ACK:
            self._on_ack_received(reply_telegram)
            return

        if reply_telegram.system_function == SystemFunction.NAK:
            self._on_nack_received(reply_telegram)
            return

        if reply_telegram.system_function == SystemFunction.ACTIONTABLE:
            self._on_actiontable_chunk_received(reply_telegram)
            return

        if reply_telegram.system_function == SystemFunction.EOF:
            self._on_eof_received(reply_telegram)
            return

    def _on_timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Timeout occurred")
        if self.receiving.is_active:
            self.do_timeout()  # receiving -> resetting
        elif self.waiting_ok.is_active:
            self.do_timeout()  # waiting_ok -> receiving
        elif self.receiving2.is_active:
            self.do_timeout2()  # receiving2 -> resetting2
        elif self.waiting_ok2.is_active:
            self.do_timeout2()  # waiting_ok2 -> receiving2
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

    def start(
        self,
        serial_number: str,
        timeout_seconds: Optional[float] = 2.0,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            serial_number: Module serial number.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting actiontable download")
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

    def __enter__(self) -> "ActionTableDownloadService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.actiontable_data = []
        self._download_complete = False
        # Reset state machine to idle
        self._reset_state()
        return self

    def _reset_state(self) -> None:
        """Reset state machine to initial state."""
        # python-statemachine uses model.state to track current state
        # Set it directly to the initial state id
        self.model.state = self.idle.id
        self._download_complete = False

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        # Disconnect protocol signals
        self.conbus_protocol.on_connection_made.disconnect(self._on_connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self._on_telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self._on_telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self._on_timeout)
        self.conbus_protocol.on_failed.disconnect(self._on_failed)
        # Disconnect service signals
        self.on_progress.disconnect()
        self.on_error.disconnect()
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
