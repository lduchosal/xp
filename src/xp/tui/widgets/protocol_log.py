"""Protocol Log Widget for displaying telegram stream."""

import asyncio
import logging
from enum import Enum
from typing import Any, Optional

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.conbus.conbus_receive_service import ConbusReceiveService
from xp.services.protocol import ConbusEventProtocol


class ConnectionState(str, Enum):
    """Connection state enumeration.

    Attributes:
        DISCONNECTED: Not connected to server.
        CONNECTING: Connection in progress.
        CONNECTED: Successfully connected.
        FAILED: Connection failed.
    """

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"


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

    connection_state = reactive(ConnectionState.DISCONNECTED)

    def __init__(self, container: Any) -> None:
        """Initialize the Protocol Log widget.

        Args:
            container: ServiceContainer for resolving services.
        """
        super().__init__()
        self.container = container
        self.protocol: Optional[ConbusEventProtocol] = None
        self.service: Optional[ConbusReceiveService] = None
        self.logger = logging.getLogger(__name__)
        self.log_widget: Optional[RichLog] = None

    def compose(self) -> Any:
        """Compose the widget layout.

        Yields:
            RichLog widget for message display.
        """
        self.log_widget = RichLog(highlight=True, markup=True)
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
        await self._start_connection_async()

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

        try:
            # Set state to connecting
            self.connection_state = ConnectionState.CONNECTING
            if self.log_widget:
                self.log_widget.write("[yellow]Connecting to Conbus server...[/yellow]")

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
            # Schedule the connection on the running asyncio loop
            # This ensures connectTCP is called in the context of the running loop

            def do_connect() -> None:
                """Execute TCP connection in event loop context."""
                self.logger.info("Executing connectTCP in event loop callback")
                if self.protocol is not None:
                    reactor.connectTCP(
                        self.protocol.cli_config.ip,
                        self.protocol.cli_config.port,
                        self.protocol,
                    )

            event_loop.call_soon(do_connect)
            self.logger.info("Scheduled connectTCP on running loop")

            if self.log_widget:
                self.log_widget.write(
                    f"[dim]→ {self.protocol.cli_config.ip}:{self.protocol.cli_config.port}[/dim]"
                )

            # Wait for connection to establish
            await asyncio.sleep(1.0)
            self.logger.info(f"After 1s - transport: {self.protocol.transport}")

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.connection_state = ConnectionState.FAILED
            if self.log_widget:
                self.log_widget.write(f"[red]Connection error: {e}[/red]")
            # Exit app after brief delay
            self.set_timer(2.0, self.app.exit)

    def _start_connection(self) -> None:
        """Start connection (sync wrapper for async method)."""
        # Use run_worker to run async method from sync context
        self.run_worker(self._start_connection_async(), exclusive=True)

    def _on_connection_made(self) -> None:
        """Handle connection established signal.

        Sets state to CONNECTED and displays success message.
        """
        self.connection_state = ConnectionState.CONNECTED
        if self.log_widget:
            self.log_widget.write("[green]Connected to Conbus server[/green]")
            self.log_widget.write("[dim]---[/dim]")

    def _on_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle telegram received signal.

        Args:
            event: Telegram received event with frame data.
        """
        if self.log_widget:
            # Display [RX] in green, frame in gray
            self.log_widget.write(f"[green]\\[RX][/green] [dim]{event.frame}[/dim]")

    def _on_telegram_sent(self, telegram: str) -> None:
        """Handle telegram sent signal.

        Args:
            telegram: Sent telegram string.
        """
        if self.log_widget:
            # Display [TX] in green, frame in gray
            self.log_widget.write(f"[green]\\[TX][/green] [dim]{telegram}[/dim]")

    def _on_timeout(self) -> None:
        """Handle timeout signal.

        Logs timeout but continues monitoring (no action needed).
        """
        self.logger.debug("Timeout occurred (continuous monitoring)")

    def _on_failed(self, error: str) -> None:
        """Handle connection failed signal.

        Args:
            error: Error message describing the failure.
        """
        self.connection_state = ConnectionState.FAILED
        self.logger.error(f"Connection failed: {error}")

        if self.log_widget:
            self.log_widget.write(f"[red]Connection failed: {error}[/red]")

        # Exit app after brief delay to show error
        self.set_timer(2.0, self.app.exit)

    def connect(self) -> None:
        """Connect to Conbus server."""
        self._start_connection()

    def disconnect(self) -> None:
        """Disconnect from Conbus server."""
        if self.protocol:
            self.protocol.disconnect()

    def send_discover(self) -> None:
        """Send discover telegram.

        Sends predefined discover telegram <S0000000000F01D00FA> to the bus.
        Called when user presses 'd' key.
        """
        if self.protocol is None:
            self.logger.warning("Cannot send discover: not connected")
            if self.log_widget:
                self.log_widget.write(
                    "[yellow]Not connected, cannot send discover[/yellow]"
                )
            return

        try:
            # Send discover telegram
            # Note: The telegram includes framing <>, but protocol may add it
            # Check if protocol expects with or without brackets
            from xp.models.telegram.system_function import SystemFunction
            from xp.models.telegram.telegram_type import TelegramType

            # Send discover: S 0000000000 F01 D00
            self.protocol.send_telegram(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0000000000",
                system_function=SystemFunction.DISCOVERY,
                data_value="00",
            )

            if self.log_widget:
                self.log_widget.write("[yellow]Discover telegram sent[/yellow]")

        except Exception as e:
            self.logger.error(f"Failed to send discover: {e}")
            if self.log_widget:
                self.log_widget.write(f"[red]Failed to send discover: {e}[/red]")

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
