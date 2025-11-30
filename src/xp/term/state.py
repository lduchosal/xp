"""State Monitor TUI Application."""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult

from xp.services.term.state_monitor_service import StateMonitorService
from xp.term.widgets.modules_list import ModulesListWidget
from xp.term.widgets.status_footer import StatusFooterWidget


class StateMonitorApp(App[None]):
    """
    Textual app for module state monitoring.

    Displays module states from Conson configuration in an interactive
    terminal interface with real-time updates.

    Attributes:
        state_service: StateMonitorService for module state operations.
        CSS_PATH: Path to CSS stylesheet file.
        BINDINGS: Keyboard bindings for app actions.
        TITLE: Application title displayed in header.
        ENABLE_COMMAND_PALETTE: Disable Textual's command palette feature.
    """

    CSS_PATH = Path(__file__).parent / "state.tcss"
    TITLE = "Modules"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("Q", "quit", "Quit"),
        ("C", "toggle_connection", "Connect"),
        ("r", "refresh_all", "Refresh"),
    ]

    def __init__(self, state_service: StateMonitorService) -> None:
        """
        Initialize the State Monitor app.

        Args:
            state_service: StateMonitorService for module state operations.
        """
        super().__init__()
        self.state_service: StateMonitorService = state_service
        self.modules_widget: Optional[ModulesListWidget] = None
        self.footer_widget: Optional[StatusFooterWidget] = None

    def compose(self) -> ComposeResult:
        """
        Compose the app layout with widgets.

        Yields:
            ModulesListWidget and StatusFooterWidget.
        """
        self.modules_widget = ModulesListWidget(
            service=self.state_service, id="modules-list"
        )
        yield self.modules_widget

        self.footer_widget = StatusFooterWidget(
            service=self.state_service, id="footer-container"
        )
        yield self.footer_widget

    async def on_mount(self) -> None:
        """
        Initialize app after UI is mounted.

        Delays connection by 0.5s to let UI render first. Sets up automatic screen
        refresh every second to update elapsed times.
        """
        import asyncio

        # Delay connection to let UI render
        await asyncio.sleep(0.5)
        self.state_service.connect()

        # Set up periodic refresh to update elapsed times
        self.set_interval(1.0, self._refresh_last_update_column)

    def _refresh_last_update_column(self) -> None:
        """Refresh only the last_update column to show elapsed time."""
        if self.modules_widget:
            self.modules_widget.refresh_last_update_times()

    def action_toggle_connection(self) -> None:
        """
        Toggle connection on 'c' key press.

        Connects if disconnected/failed, disconnects if connected/connecting.
        """
        self.state_service.toggle_connection()

    def action_refresh_all(self) -> None:
        """Refresh all module data on 'r' key press."""
        self.state_service.refresh_all()

    def on_unmount(self) -> None:
        """Clean up service when app unmounts."""
        self.state_service.cleanup()
