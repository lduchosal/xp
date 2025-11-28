"""State machine for ActionTable download workflow."""

import logging
from enum import Enum

from statemachine import State, StateMachine

# Constants
MAX_ERROR_RETRIES = 3  # Max retries for error_status_received before giving up


class Phase(Enum):
    """Download workflow phases.

    The download workflow consists of three sequential phases:
    - INIT: Drain pending telegrams, query error status → proceed to DOWNLOAD
    - DOWNLOAD: Request actiontable, receive chunks with ACK, until EOF
    - CLEANUP: Drain pending telegrams, query error status → proceed to COMPLETED

    Attributes:
        INIT: Initial phase - drain pending telegrams and query error status.
        DOWNLOAD: Download phase - request actiontable and receive chunks.
        CLEANUP: Cleanup phase - drain remaining telegrams and verify status.
    """

    INIT = "init"
    DOWNLOAD = "download"
    CLEANUP = "cleanup"


class ActionTableDownloadStateMachine(StateMachine):
    """State machine for ActionTable download workflow.

    Pure state machine with states, transitions, and guards. Subclasses can
    override on_enter_* methods to add protocol-specific behavior.

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
    1. Drain pending telegrams (receiving state discards telegrams)
    2. Timeout triggers error status query (resetting)
    3. Wait for response (waiting_ok)
    4. On no error: guard determines target (requesting or completed)
       On error: retry from drain step (limited by MAX_ERROR_RETRIES)

    Attributes:
        phase: Current workflow phase (INIT, DOWNLOAD, CLEANUP).
        error_retry_count: Current error retry count.
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
    error_status_received = waiting_ok.to(
        receiving, cond="can_retry"
    )  # Retry if under limit

    # Conditional transitions based on phase
    no_error_status_received = waiting_ok.to(
        requesting, cond="is_init_phase"
    ) | waiting_ok.to(completed, cond="is_cleanup_phase")

    # DOWNLOAD phase transitions
    send_download = requesting.to(waiting_data)
    receive_chunk = waiting_data.to(receiving_chunk)
    send_ack = receiving_chunk.to(waiting_data)
    receive_eof = waiting_data.to(processing_eof)

    # Return to drain/reset cycle for CLEANUP phase
    do_finish = processing_eof.to(receiving)

    def __init__(self) -> None:
        """Initialize the state machine."""
        self.logger = logging.getLogger(__name__)
        self._phase: Phase = Phase.INIT
        self._error_retry_count: int = 0

        # Initialize state machine
        super().__init__(allow_event_without_transition=True)

    @property
    def phase(self) -> Phase:
        """Get current phase."""
        return self._phase

    @phase.setter
    def phase(self, value: Phase) -> None:
        """Set current phase."""
        self._phase = value

    @property
    def error_retry_count(self) -> int:
        """Get current error retry count."""
        return self._error_retry_count

    @error_retry_count.setter
    def error_retry_count(self, value: int) -> None:
        """Set error retry count."""
        self._error_retry_count = value

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

    # State entry hooks - subclasses can override these

    def on_enter_receiving(self) -> None:
        """Enter receiving state - drain pending telegrams."""
        self.logger.debug(f"Entering RECEIVING state (phase={self._phase.value})")

    def on_enter_resetting(self) -> None:
        """Enter resetting state - query error status."""
        self.logger.debug(f"Entering RESETTING state (phase={self._phase.value})")

    def on_enter_waiting_ok(self) -> None:
        """Enter waiting_ok state - awaiting error status response."""
        self.logger.debug(f"Entering WAITING_OK state (phase={self._phase.value})")

    def on_enter_requesting(self) -> None:
        """Enter requesting state - send download request."""
        self.logger.debug("Entering REQUESTING state - sending download request")

    def enter_download_phase(self) -> None:
        """Enter requesting state - send download request."""
        self._phase = Phase.DOWNLOAD

    def on_enter_waiting_data(self) -> None:
        """Enter waiting_data state - wait for actiontable chunks."""
        self.logger.debug("Entering WAITING_DATA state - awaiting chunks")

    def on_enter_receiving_chunk(self) -> None:
        """Enter receiving_chunk state - send ACK."""
        self.logger.debug("Entering RECEIVING_CHUNK state - sending ACK")

    def on_enter_processing_eof(self) -> None:
        """Enter processing_eof state - deserialize and emit result."""
        self.logger.debug("Entering PROCESSING_EOF state - deserializing")

    def on_enter_completed(self) -> None:
        """Enter completed state - download finished."""
        self.logger.debug("Entering COMPLETED state - download finished")

    # Callback for max retries exceeded - subclasses can override

    def on_max_retries_exceeded(self) -> None:
        """Called when max error retries exceeded. Override in subclass."""
        self.logger.error(f"Max error retries ({MAX_ERROR_RETRIES}) exceeded")

    # Public methods for state machine control

    def handle_no_error_received(self) -> None:
        """Handle successful error status check (no error)."""
        self._error_retry_count = 0  # Reset on success
        self.no_error_status_received()

    def handle_error_received(self) -> None:
        """Handle error status received - increment retry and attempt transition."""
        self._error_retry_count += 1
        self.logger.debug(
            f"Error status received, retry {self._error_retry_count}/{MAX_ERROR_RETRIES}"
        )
        # Guard can_retry blocks transition if max retries exceeded
        self.error_status_received()
        # Check if guard blocked the transition (still in waiting_ok)
        if self.waiting_ok.is_active:
            self.on_max_retries_exceeded()

    def start_cleanup_phase(self) -> None:
        """Switch to CLEANUP phase and trigger do_finish transition."""
        self._phase = Phase.CLEANUP
        self.do_finish()

    def reset(self) -> None:
        """Reset state machine to initial state."""
        self._phase = Phase.INIT
        self._error_retry_count = 0
        # python-statemachine uses model.state to track current state
        self.model.state = self.idle.id
