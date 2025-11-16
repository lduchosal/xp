"""Protocol Monitor TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Static

from xp.models.term import ProtocolKeysConfig
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
        ("c", "toggle_connection", "Connect"),
        ("r", "reset", "Reset"),
        ("0-9,a-c", "protocol_keys", "Keys"),
        ("h", "toggle_help", "Help"),
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
        self.help_table: Optional[DataTable] = None
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
        self.protocol_widget = ProtocolLogWidget(container=self.container)
        yield self.protocol_widget

        # Help menu (hidden by default)
        with Vertical(id="help-menu"):
            yield Static("Protocol Keys", id="help-title")
            self.help_table = DataTable(id="help-table")
            yield self.help_table

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

    def action_reset(self) -> None:
        """Reset and clear protocol widget on 'r' key press."""
        if self.protocol_widget:
            self.protocol_widget.clear_log()

    def action_toggle_help(self) -> None:
        """Toggle help menu visibility on 'h' key press."""
        help_menu = self.query_one("#help-menu")
        if help_menu.styles.display == "none":
            help_menu.styles.display = "block"
        else:
            help_menu.styles.display = "none"

    def on_key(self, event: Any) -> None:
        """Handle key press events for protocol keys.

        Args:
            event: Key press event from Textual.
        """
        if event.key in self.protocol_keys.protocol and self.protocol_widget:
            key_config = self.protocol_keys.protocol[event.key]
            for telegram in key_config.telegrams:
                self.protocol_widget.send_telegram(telegram)

    def on_mount(self) -> None:
        """Set up status line updates when app mounts."""
        if self.protocol_widget:
            self.protocol_widget.watch(
                self.protocol_widget,
                "connection_state",
                self._update_status,
            )

        # Initialize help table
        if self.help_table:
            self.help_table.add_columns("Key", "Command")
            for key, config in self.protocol_keys.protocol.items():
                self.help_table.add_row(key, config.name)

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
