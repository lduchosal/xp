"""HomeKit TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult

from xp.services.term.homekit_service import HomekitService
from xp.term.widgets.room_list import RoomListWidget
from xp.term.widgets.status_footer import StatusFooterWidget


class HomekitApp(App[None]):
    """
    Textual app for HomeKit accessory monitoring.

    Displays rooms and accessories with real-time state updates
    and toggle control via action keys.

    Attributes:
        homekit_service: HomekitService for accessory state operations.
        CSS_PATH: Path to CSS stylesheet file.
        BINDINGS: Keyboard bindings for app actions.
        TITLE: Application title displayed in header.
        ENABLE_COMMAND_PALETTE: Disable Textual's command palette feature.
    """

    CSS_PATH = Path(__file__).parent / "homekit.tcss"
    TITLE = "HomeKit"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("Q", "quit", "Quit"),
        ("C", "toggle_connection", "Connect"),
        ("r", "refresh_all", "Refresh"),
    ]

    def __init__(self, homekit_service: HomekitService) -> None:
        """
        Initialize the HomeKit app.

        Args:
            homekit_service: HomekitService for accessory state operations.
        """
        super().__init__()
        self.homekit_service: HomekitService = homekit_service
        self.room_list_widget: Optional[RoomListWidget] = None
        self.footer_widget: Optional[StatusFooterWidget] = None

    def compose(self) -> ComposeResult:
        """
        Compose the app layout with widgets.

        Yields:
            RoomListWidget and StatusFooterWidget.
        """
        self.room_list_widget = RoomListWidget(
            service=self.homekit_service, id="room-list"
        )
        yield self.room_list_widget

        self.footer_widget = StatusFooterWidget(
            service=self.homekit_service, id="footer-container"
        )
        yield self.footer_widget

    async def on_mount(self) -> None:
        """
        Initialize app after UI is mounted.

        Delays connection by 0.5s to let UI render first. Starts the AccessoryDriver and
        sets up automatic screen refresh every second to update elapsed times.
        """
        import asyncio

        # Delay connection to let UI render
        await asyncio.sleep(0.5)
        await self.homekit_service.start()

        # Set up periodic refresh to update elapsed times
        self.set_interval(1.0, self._refresh_last_update_column)

    def _refresh_last_update_column(self) -> None:
        """Refresh only the last_update column to show elapsed time."""
        if self.room_list_widget:
            self.room_list_widget.refresh_last_update_times()

    def on_key(self, event: Any) -> None:
        """
        Handle key press events for action keys.

        Intercepts a-z0-9 keys to toggle accessories.

        Args:
            event: Key press event.
        """
        key = event.key.lower()
        if len(key) == 1 and (("a" <= key <= "z") or ("0" <= key <= "9")):
            if self.homekit_service.toggle_accessory(key):
                event.prevent_default()

    def action_toggle_connection(self) -> None:
        """
        Toggle connection on 'c' key press.

        Connects if disconnected/failed, disconnects if connected/connecting.
        """
        self.homekit_service.toggle_connection()

    def action_refresh_all(self) -> None:
        """Refresh all module data on 'r' key press."""
        self.homekit_service.refresh_all()

    async def on_unmount(self) -> None:
        """Stop AccessoryDriver and clean up service when app unmounts."""
        await self.homekit_service.stop()
