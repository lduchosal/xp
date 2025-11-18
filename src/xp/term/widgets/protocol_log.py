"""Protocol Log Widget for displaying telegram stream."""

import asyncio
import logging
from typing import Any, Optional

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog
from twisted.python.failure import Failure

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.term.connection_state import ConnectionState
from xp.models.term.status_message import StatusMessageChanged
from xp.services.protocol import ConbusEventProtocol


class ProtocolLogWidget(Widget):
    """Widget for displaying protocol telegram stream.

    Connects to Conbus server via ConbusReceiveService and displays
    live RX/TX telegram stream with color-coded direction markers.

    Attributes:
        container: ServiceContainer for dependency injection.
        connection_state: Current connection state (reactive).
        protocol: Reference to ConbusEventProtocol (prevents duplicate connections).
        logger: Logger instance for this widget.
        log_widget: RichLog widget for displaying messages.
    """

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
        self.logger = logging.getLogger(__name__)
        self.log_widget: Optional[RichLog] = None
        self._state_machine = ConnectionState.create_state_machine()

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
        self.protocol = self.container.resolve(ConbusEventProtocol)

        # Connect psygnal signals
        self.protocol.on_connection_made.connect(self._on_connection_made)
        self.protocol.on_connection_failed.connect(self._on_connection_failed)
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
                self.post_status(
                    f"Connecting to {self.protocol.cli_config.ip}:{self.protocol.cli_config.port}..."
                )

            # Connect to server (auto-detects and integrates with asyncio event loop)
            self.protocol.connect()

            # Wait for connection to establish
            await asyncio.sleep(1.0)
            self.logger.info(f"After 1s - transport: {self.protocol.transport}")

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.post_status(f"Connection failed: {e}")
            # Transition to FAILED
            if self._state_machine.transition("failed", ConnectionState.FAILED):
                self.connection_state = ConnectionState.FAILED

    def _start_connection(self) -> None:
        """Start connection (sync wrapper for async method)."""
        # Use run_worker to run async method from sync context
        self.logger.debug("Start connection")
        self.post_status("Start connection")
        self.run_worker(self._start_connection_async(), exclusive=True)

    def _on_connection_made(self) -> None:
        """Handle connection established signal.

        Sets state to CONNECTED and displays success message.
        """
        self.logger.debug("Connection made")
        self.post_status("Connection made")
        # Transition to CONNECTED
        if self._state_machine.transition("connected", ConnectionState.CONNECTED):
            self.connection_state = ConnectionState.CONNECTED
            if self.protocol:
                self.post_status(
                    f"Connected to {self.protocol.cli_config.ip}:{self.protocol.cli_config.port}"
                )

    def _on_connection_failed(self, failure: Failure) -> None:
        """Handle connection failed signal.

        Sets state to DISCONNECTED and displays success message.
        """
        self.logger.debug("Connection failed")
        self.post_status(failure.getErrorMessage())
        # Transition to CONNECTED
        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self.connection_state = ConnectionState.DISCONNECTED

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
            self.post_status(f"Failed: {error}")

    def post_status(self, message: str) -> None:
        """Post status message.

        Args:
            message: message to be sent to status bar.
        """
        self.post_message(StatusMessageChanged(message))

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
        if self._state_machine.transition(
            "disconnecting", ConnectionState.DISCONNECTING
        ):
            self.connection_state = ConnectionState.DISCONNECTING
            self.post_status("Disconnecting...")

        if self.protocol:
            self.protocol.disconnect()

        # Transition to DISCONNECTED
        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self.connection_state = ConnectionState.DISCONNECTED
            self.post_status("Disconnected")

    def send_telegram(self, name: str, telegram: str) -> None:
        """Send a raw telegram string.

        Args:
            name: Telegram name (e.g., "Discover")
            telegram: Telegram string including angle brackets (e.g., "S0000000000F01D00")
        """
        if self.protocol is None:
            self.logger.warning("Cannot send telegram: not connected")
            return

        try:
            # Remove angle brackets if present
            self.post_status(f"{name} sent.")
            # Send raw telegram
            self.protocol.send_raw_telegram(telegram)

        except Exception as e:
            self.logger.error(f"Failed to send telegram: {e}")
            self.post_status(f"Failed: {e}")

    def clear_log(self) -> None:
        """Clear the protocol log widget."""
        if self.log_widget:
            self.log_widget.clear()
            self.post_status("Log cleared")

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
