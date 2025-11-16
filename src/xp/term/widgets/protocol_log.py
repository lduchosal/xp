"""Protocol Log Widget for displaying telegram stream."""

import asyncio
import logging
from enum import Enum
from typing import Any, Optional

from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.conbus.conbus_receive_service import ConbusReceiveService
from xp.services.protocol import ConbusEventProtocol
from xp.utils.state_machine import StateMachine


class ConnectionState(str, Enum):
    """Connection state enumeration.

    Attributes:
        DISCONNECTING: Disconnecting to server.
        DISCONNECTED: Not connected to server.
        CONNECTING: Connection in progress.
        CONNECTED: Successfully connected.
        FAILED: Connection failed.
    """

    DISCONNECTING = "DISCONNECTING"
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"


def create_connection_state_machine() -> StateMachine:
    """Create and configure state machine for connection management.

    Returns:
        Configured StateMachine with connection state transitions.
    """
    sm = StateMachine(ConnectionState.DISCONNECTED)

    # Define valid transitions
    sm.define_transition("connect", {ConnectionState.DISCONNECTED, ConnectionState.FAILED})
    sm.define_transition("disconnect", {ConnectionState.CONNECTED, ConnectionState.CONNECTING})
    sm.define_transition("connecting", {ConnectionState.DISCONNECTED, ConnectionState.FAILED})
    sm.define_transition("connected", {ConnectionState.CONNECTING})
    sm.define_transition("disconnecting", {ConnectionState.CONNECTED, ConnectionState.CONNECTING})
    sm.define_transition("disconnected", {ConnectionState.DISCONNECTING})
    sm.define_transition(
        "failed",
        {
            ConnectionState.CONNECTING,
            ConnectionState.CONNECTED,
            ConnectionState.DISCONNECTING,
        },
    )

    return sm


class ProtocolLogWidget(Widget):
    """Widget for displaying protocol telegram stream.

    Connects to Conbus server via ConbusReceiveService and displays
    live RX/TX telegram stream with color-coded direction markers.

    Attributes:
        container: ServiceContainer for dependency injection.
        connection_state: Current connection state (reactive).
        protocol: Reference to ConbusEventProtocol (prevents duplicate connections).
        service: ConbusReceiveService instance.
        logger: Logger instance for this widget.
        log_widget: RichLog widget for displaying messages.
    """

    class StatusMessageChanged(Message):
        """Message posted when status message changes."""

        def __init__(self, message: str) -> None:
            """Initialize the message.

            Args:
                message: The status message to display.
            """
            super().__init__()
            self.message = message

    connection_state = reactive(ConnectionState.DISCONNECTED)

    def __init__(self, container: Any) -> None:
        """Initialize the Protocol Log widget.

        Args:
            container: ServiceContainer for resolving services.
        """
        super().__init__()
        self.border_title = "Protocol"
        self.container = container
        self.protocol: Optional[ConbusEventProtocol] = None
        self.service: Optional[ConbusReceiveService] = None
        self.logger = logging.getLogger(__name__)
        self.log_widget: Optional[RichLog] = None
        self._state_machine = create_connection_state_machine()

    def compose(self) -> Any:
        """Compose the widget layout.

        Yields:
            RichLog widget for message display.
        """
        self.log_widget = RichLog(highlight=False, markup=True)
        yield self.log_widget

    async def on_mount(self) -> None:
        """Initialize connection when widget mounts.

        Delays connection by 0.5s to let UI render first.
        Resolves ConbusReceiveService and connects signals.
        """
        # Resolve service from container (singleton)
        self.service = self.container.resolve(ConbusReceiveService)
        self.protocol = self.service.conbus_protocol

        # Connect psygnal signals
        self.protocol.on_connection_made.connect(self._on_connection_made)
        self.protocol.on_telegram_received.connect(self._on_telegram_received)
        self.protocol.on_telegram_sent.connect(self._on_telegram_sent)
        self.protocol.on_timeout.connect(self._on_timeout)
        self.protocol.on_failed.connect(self._on_failed)

        # Delay connection to let UI render
        await asyncio.sleep(0.5)
        self._start_connection()

    async def _start_connection_async(self) -> None:
        """Start TCP connection to Conbus server (async).

        Guards against duplicate connections and sets up protocol signals.
        Integrates Twisted reactor with Textual's asyncio loop cleanly.
        """
        # Guard against duplicate connections (race condition)
        if self.service is None:
            self.logger.error("Service not initialized")
            return

        if self.protocol is None:
            self.logger.error("Protocol not initialized")
            return

        # Guard: Don't connect if already connected or connecting
        if not self._state_machine.can_transition("connecting"):
            self.logger.warning(
                f"Already {self._state_machine.get_state().value}, ignoring connect request"
            )
            return

        try:
            # Transition to CONNECTING
            if self._state_machine.transition("connecting", ConnectionState.CONNECTING):
                self.connection_state = ConnectionState.CONNECTING
                self.post_message(
                    self.StatusMessageChanged(
                        f"Connecting to {self.protocol.cli_config.ip}:{self.protocol.cli_config.port}..."
                    )
                )

            # Store protocol reference
            self.logger.info(f"Protocol object: {self.protocol}")
            self.logger.info(f"Reactor object: {self.protocol._reactor}")
            self.logger.info(f"Reactor running: {self.protocol._reactor.running}")

            # Setup service callbacks
            def progress_callback(telegram: str) -> None:
                """Handle progress updates for telegram reception.

                Args:
                    telegram: Received telegram string.
                """
                pass

            def finish_callback(response: Any) -> None:
                """Handle completion of telegram reception.

                Args:
                    response: Response object from telegram reception.
                """
                pass

            # Get the currently running asyncio event loop (Textual's loop)
            event_loop = asyncio.get_running_loop()
            self.logger.info(f"Current running loop: {event_loop}")
            self.logger.info(f"Loop is running: {event_loop.is_running()}")

            self.service.init(
                progress_callback=progress_callback,
                finish_callback=finish_callback,
                timeout_seconds=None,  # Continuous monitoring
                event_loop=event_loop,
            )

            reactor = self.service.conbus_protocol._reactor
            reactor.connectTCP(
                self.protocol.cli_config.ip,
                self.protocol.cli_config.port,
                self.protocol,
            )

            # Wait for connection to establish
            await asyncio.sleep(1.0)
            self.logger.info(f"After 1s - transport: {self.protocol.transport}")

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            # Transition to FAILED
            if self._state_machine.transition("failed", ConnectionState.FAILED):
                self.connection_state = ConnectionState.FAILED
                self.post_message(self.StatusMessageChanged(f"Connection error: {e}"))

    def _start_connection(self) -> None:
        """Start connection (sync wrapper for async method)."""
        # Use run_worker to run async method from sync context
        self.logger.debug("Start connection")
        self.run_worker(self._start_connection_async(), exclusive=True)

    def _on_connection_made(self) -> None:
        """Handle connection established signal.

        Sets state to CONNECTED and displays success message.
        """
        self.logger.debug("Connection made")
        # Transition to CONNECTED
        if self._state_machine.transition("connected", ConnectionState.CONNECTED):
            self.connection_state = ConnectionState.CONNECTED
            if self.protocol:
                self.post_message(
                    self.StatusMessageChanged(
                        f"Connected to {self.protocol.cli_config.ip}:{self.protocol.cli_config.port}"
                    )
                )

    def _on_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle telegram received signal.

        Args:
            event: Telegram received event with frame data.
        """
        self.logger.debug("Telegram received")
        if self.log_widget:
            # Display [RX] and frame in bright green
            self.log_widget.write(f"[#00ff00]\\[RX] {event.frame}[/#00ff00]")

    def _on_telegram_sent(self, telegram: str) -> None:
        """Handle telegram sent signal.

        Args:
            telegram: Sent telegram string.
        """
        self.logger.debug("Telegram sent")
        if self.log_widget:
            # Display [TX] and frame in bold bright green
            self.log_widget.write(f"[bold #00ff00]\\[TX] {telegram}[/bold #00ff00]")

    def _on_timeout(self) -> None:
        """Handle timeout signal.

        Logs timeout but continues monitoring (no action needed).
        """
        self.logger.debug("Timeout")
        self.logger.debug("Timeout occurred (continuous monitoring)")

    def _on_failed(self, error: str) -> None:
        """Handle connection failed signal.

        Args:
            error: Error message describing the failure.
        """
        # Transition to FAILED
        if self._state_machine.transition("failed", ConnectionState.FAILED):
            self.connection_state = ConnectionState.FAILED
            self.logger.error(f"Connection failed: {error}")
            self.post_message(self.StatusMessageChanged(f"Failed: {error}"))

    def connect(self) -> None:
        """Connect to Conbus server.

        Only initiates connection if currently DISCONNECTED or FAILED.
        """
        self.logger.debug("Connect")

        # Guard: Check if connection is allowed
        if not self._state_machine.can_transition("connect"):
            self.logger.warning(
                f"Cannot connect: current state is {self._state_machine.get_state().value}"
            )
            return

        self._start_connection()

    def disconnect(self) -> None:
        """Disconnect from Conbus server.

        Only disconnects if currently CONNECTED or CONNECTING.
        """
        self.logger.debug("Disconnect")

        # Guard: Check if disconnection is allowed
        if not self._state_machine.can_transition("disconnect"):
            self.logger.warning(
                f"Cannot disconnect: current state is {self._state_machine.get_state().value}"
            )
            return

        # Transition to DISCONNECTING
        if self._state_machine.transition("disconnecting", ConnectionState.DISCONNECTING):
            self.connection_state = ConnectionState.DISCONNECTING
            self.post_message(self.StatusMessageChanged("Disconnecting..."))

        if self.protocol:
            self.protocol.disconnect()

        # Transition to DISCONNECTED
        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self.connection_state = ConnectionState.DISCONNECTED
            self.post_message(self.StatusMessageChanged("Disconnected"))

    def send_telegram(self, telegram: str) -> None:
        """Send a raw telegram string.

        Args:
            telegram: Telegram string including angle brackets (e.g., "<S0000000000F01D00FA>")
        """
        if self.protocol is None:
            self.logger.warning("Cannot send telegram: not connected")
            return

        try:
            # Remove angle brackets if present
            clean_telegram = telegram.strip("<>")
            self.post_message(self.StatusMessageChanged(f"Sending {telegram}..."))

            # Send raw telegram
            self.protocol.send_raw_telegram(clean_telegram)

        except Exception as e:
            self.logger.error(f"Failed to send telegram: {e}")
            self.post_message(self.StatusMessageChanged(f"Failed: {e}"))

    def clear_log(self) -> None:
        """Clear the protocol log widget."""
        if self.log_widget:
            self.log_widget.clear()
            self.post_message(self.StatusMessageChanged("Log cleared"))

    def on_unmount(self) -> None:
        """Clean up when widget unmounts.

        Disconnects signals and closes transport connection.
        """
        if self.protocol is not None:
            try:
                # Disconnect all signals
                self.protocol.on_connection_made.disconnect(self._on_connection_made)
                self.protocol.on_telegram_received.disconnect(
                    self._on_telegram_received
                )
                self.protocol.on_telegram_sent.disconnect(self._on_telegram_sent)
                self.protocol.on_timeout.disconnect(self._on_timeout)
                self.protocol.on_failed.disconnect(self._on_failed)

                # Close transport if connected
                if self.protocol.transport:
                    self.protocol.disconnect()

                # Reset protocol reference
                self.protocol = None

                # Set state to disconnected
                self.connection_state = ConnectionState.DISCONNECTED

            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
