"""Protocol Monitor TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from xp.models.term import ProtocolKeysConfig
from xp.models.term.status_message import StatusMessageChanged
from xp.term.widgets.help_menu import HelpMenuWidget
from xp.term.widgets.protocol_log import ProtocolLogWidget
from xp.term.widgets.status_footer import StatusFooterWidget


class ProtocolMonitorApp(App[None]):
    """Textual app for real-time protocol monitoring.

    Displays live RX/TX telegram stream from Conbus server in an interactive
    terminal interface with keyboard shortcuts for control.

    Attributes:
        container: ServiceContainer for dependency injection.
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

    def __init__(self, container: Any) -> None:
        """Initialize the Protocol Monitor app.

        Args:
            container: ServiceContainer for resolving services.
        """
        super().__init__()
        self.container = container

        # Import here to avoid circular dependency
        from xp.services.term.protocol_monitor_service import ProtocolMonitorService

        self.protocol_service = container.resolve(ProtocolMonitorService)
        self.protocol_widget: Optional[ProtocolLogWidget] = None
        self.help_menu: Optional[HelpMenuWidget] = None
        self.footer_widget: Optional[StatusFooterWidget] = None
        self.protocol_keys = self._load_protocol_keys()

    def _load_protocol_keys(self) -> ProtocolKeysConfig:
        """Load protocol keys from YAML config file.

        Returns:
            ProtocolKeysConfig instance.
        """
        config_path = Path(__file__).parent / "protocol.yml"
        return ProtocolKeysConfig.from_yaml(config_path)

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
                protocol_keys=self.protocol_keys, id="help-menu"
            )
            yield self.help_menu

        self.footer_widget = StatusFooterWidget(id="footer-container")
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

    def on_mount(self) -> None:
        """Set up status line updates when app mounts."""
        if self.protocol_widget and self.footer_widget:
            self.protocol_service.on_connection_state_changed.connect(
                self.footer_widget.update_status
            )

    def on_key(self, event: Any) -> None:
        """Handle key press events for protocol keys.

        Args:
            event: Key press event from Textual.
        """
        if event.key in self.protocol_keys.protocol and self.protocol_widget:
            key_config = self.protocol_keys.protocol[event.key]
            for telegram in key_config.telegrams:
                self.protocol_widget.send_telegram(key_config.name, telegram)

    def on_status_message_changed(self, message: StatusMessageChanged) -> None:
        """Handle status message changes from protocol widget.

        Args:
            message: Message containing the status text.
        """
        if self.footer_widget:
            self.footer_widget.update_message(message.message)
