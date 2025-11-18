"""Protocol Monitor TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from xp.term.widgets.help_menu import HelpMenuWidget
from xp.term.widgets.protocol_log import ProtocolLogWidget
from xp.term.widgets.status_footer import StatusFooterWidget


class ProtocolMonitorApp(App[None]):
    """Textual app for real-time protocol monitoring.

    Displays live RX/TX telegram stream from Conbus server in an interactive
    terminal interface with keyboard shortcuts for control.

    Attributes:
        protocol_service: ProtocolMonitorService for protocol operations.
        CSS_PATH: Path to CSS stylesheet file.
        BINDINGS: Keyboard bindings for app actions.
        TITLE: Application title displayed in header.
        ENABLE_COMMAND_PALETTE: Disable Textual's command palette feature.
    """

    CSS_PATH = Path(__file__).parent / "protocol.tcss"
    TITLE = "Protocol Monitor"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("Q", "quit", "Quit"),
        ("C", "toggle_connection", "Connect"),
        ("R", "reset", "Reset"),
        ("0-9,a-q", "protocol_keys", "Keys"),
    ]

    def __init__(self, protocol_service: Any) -> None:
        """Initialize the Protocol Monitor app.

        Args:
            protocol_service: ProtocolMonitorService for protocol operations.
        """
        super().__init__()
        self.protocol_service = protocol_service
        self.protocol_widget: Optional[ProtocolLogWidget] = None
        self.help_menu: Optional[HelpMenuWidget] = None
        self.footer_widget: Optional[StatusFooterWidget] = None

    def compose(self) -> ComposeResult:
        """Compose the app layout with widgets.

        Yields:
            ProtocolLogWidget and Footer widgets.
        """
        with Horizontal(id="main-container"):
            self.protocol_widget = ProtocolLogWidget(service=self.protocol_service)
            yield self.protocol_widget

            # Help menu (hidden by default)
            self.help_menu = HelpMenuWidget(
                protocol_keys=self.protocol_service.protocol_keys, id="help-menu"
            )
            yield self.help_menu

        self.footer_widget = StatusFooterWidget(
            service=self.protocol_service, id="footer-container"
        )
        yield self.footer_widget

    def action_toggle_connection(self) -> None:
        """Toggle connection on 'c' key press.

        Connects if disconnected/failed, disconnects if connected/connecting.
        """
        from xp.models.term.connection_state import ConnectionState

        state = self.protocol_service.connection_state
        if state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            self.protocol_service.disconnect()
        else:
            self.protocol_service.connect()

    def action_reset(self) -> None:
        """Reset and clear protocol widget on 'r' key press."""
        if self.protocol_widget:
            self.protocol_widget.clear_log()

    def on_key(self, event: Any) -> None:
        """Handle key press events for protocol keys.

        Args:
            event: Key press event from Textual.
        """
        if event.key in self.protocol_service.protocol_keys.protocol:
            key_config = self.protocol_service.protocol_keys.protocol[event.key]
            for telegram in key_config.telegrams:
                self.protocol_service.send_telegram(key_config.name, telegram)
