"""Protocol Monitor TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Static

from xp.term.widgets.protocol_log import ProtocolLogWidget


class ProtocolMonitorApp(App[None]):
    """Textual app for real-time protocol monitoring.

    Displays live RX/TX telegram stream from Conbus server in an interactive
    terminal interface with keyboard shortcuts for control.

    Attributes:
        container: ServiceContainer for dependency injection.
        CSS_PATH: Path to CSS stylesheet file.
        BINDINGS: Keyboard bindings for app actions.
        TITLE: Application title displayed in header.
    """

    CSS_PATH = Path(__file__).parent / "protocol.tcss"
    TITLE = "Protocol Monitor"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "toggle_connection", "Connect/Disconnect"),
        ("1", "discover", "Discover"),
    ]

    def __init__(self, container: Any) -> None:
        """Initialize the Protocol Monitor app.

        Args:
            container: ServiceContainer for resolving services.
        """
        super().__init__()
        self.container = container
        self.protocol_widget: Optional[ProtocolLogWidget] = None
        self.status_widget: Optional[Static] = None
        self.status_text_widget: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the app layout with widgets.

        Yields:
            ProtocolLogWidget and Footer widgets.
        """
        self.protocol_widget = ProtocolLogWidget(container=self.container)
        yield self.protocol_widget
        with Horizontal(id="footer-container"):
            yield Footer()
            self.status_text_widget = Static("", id="status-text")
            yield self.status_text_widget
            self.status_widget = Static("○", id="status-line")
            yield self.status_widget

    def action_toggle_connection(self) -> None:
        """Toggle connection on 'c' key press.

        Connects if disconnected/failed, disconnects if connected/connecting.
        """
        if self.protocol_widget:
            from xp.term.widgets.protocol_log import ConnectionState

            state = self.protocol_widget.connection_state
            if state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
                self.protocol_widget.disconnect()
            else:
                self.protocol_widget.connect()

    def action_discover(self) -> None:
        """Send discover telegram on '1' key press.

        Sends predefined discover telegram <S0000000000F01D00FA> to the bus.
        """
        if self.protocol_widget:
            self.protocol_widget.send_discover()

    def on_mount(self) -> None:
        """Set up status line updates when app mounts."""
        if self.protocol_widget:
            self.protocol_widget.watch(
                self.protocol_widget,
                "connection_state",
                self._update_status,
            )

    def _update_status(self, state: Any) -> None:
        """Update status line with connection state.

        Args:
            state: Current connection state.
        """
        if self.status_widget:
            # Map states to colored dots
            status_map = {
                "CONNECTED": "[green]●[/green]",
                "CONNECTING": "[yellow]●[/yellow]",
                "DISCONNECTING": "[yellow]●[/yellow]",
                "FAILED": "[red]●[/red]",
                "DISCONNECTED": "○",
            }
            dot = status_map.get(state.value, "○")
            self.status_widget.update(dot)

    def on_protocol_log_widget_status_message_changed(
        self, message: ProtocolLogWidget.StatusMessageChanged
    ) -> None:
        """Handle status message changes from protocol widget.

        Args:
            message: Message containing the status text.
        """
        if self.status_text_widget:
            self.status_text_widget.update(message.message)
