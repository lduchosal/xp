"""Protocol Monitor TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from xp.tui.widgets.protocol_log import ProtocolLogWidget


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

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "connect", "Connect"),
        ("d", "disconnect", "Disconnect"),
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

    def compose(self) -> ComposeResult:
        """Compose the app layout with widgets.

        Yields:
            Header, ProtocolLogWidget, and Footer widgets.
        """
        yield Header()
        self.protocol_widget = ProtocolLogWidget(container=self.container)
        yield self.protocol_widget
        yield Footer()

    def action_discover(self) -> None:
        """Send discover telegram on 'D' key press.

        Sends predefined discover telegram <S0000000000F01D00FA> to the bus.
        """
        if self.protocol_widget:
            self.protocol_widget.send_discover()

    def action_connect(self) -> None:
        """Connect protocol on 'c' key press."""
        if self.protocol_widget:
            self.protocol_widget.connect()

    def action_disconnect(self) -> None:
        """Disconnect protocol on 'd' key press."""
        if self.protocol_widget:
            self.protocol_widget.disconnect()
