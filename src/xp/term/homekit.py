"""HomeKit TUI Application."""

from pathlib import Path
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import DataTable

from xp.services.term.homekit_service import HomekitService
from xp.term.widgets.room_list import RoomListWidget
from xp.term.widgets.status_footer import StatusFooterWidget


class HomekitApp(App[None]):
    """
    Textual app for HomeKit accessory monitoring.

    Displays rooms and accessories with real-time state updates.
    Select accessory with action key, then perform action on selection.

    Attributes:
        homekit_service: HomekitService for accessory state operations.
        selected_accessory_id: Currently selected accessory ID.
        _last_cursor_row: Last cursor row for direction detection.
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
        ("R", "refresh_all", "Refresh"),
        ("space", "toggle_selected", "Toggle"),
        ("full_stop", "turn_on_selected", "On"),
        ("minus", "turn_off_selected", "Off"),
        ("plus", "dim_up", "Dim+"),
        ("quotation_mark", "dim_down", "Dim-"),
        ("asterisk", "level_up", "Level+"),
        ("ç", "level_down", "Level-"),
    ]

    def __init__(self, homekit_service: HomekitService) -> None:
        """
        Initialize the HomeKit app.

        Args:
            homekit_service: HomekitService for accessory state operations.
        """
        super().__init__()
        self.homekit_service: HomekitService = homekit_service
        self.selected_accessory_id: Optional[str] = None
        self._last_cursor_row: int = 0
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
        Handle key press events for selection and action keys.

        Selection keys (a-z0-9): Select accessory row.
        Action keys (on selected accessory):
        - Space: Toggle
        - . : Turn ON
        - - : Turn OFF
        - + : Dim up
        - " : Dim down
        - * : Level up
        - ç : Level down

        Args:
            event: Key press event.
        """
        key = event.key

        # Debug: show received key
        self.homekit_service.on_status_message.emit(f"Key: {key}")

        # Selection keys (a-z0-9)
        if len(key) == 1 and (("a" <= key <= "z") or ("0" <= key <= "9")):
            accessory_id = self.homekit_service.select_accessory(key)
            if accessory_id:
                self.selected_accessory_id = accessory_id
                self._select_row(key)
                event.prevent_default()
            return

        # Action keys (require selection)
        if not self.selected_accessory_id:
            return

        if key == "space":
            self.homekit_service.toggle_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key in ("full_stop", "."):
            self.homekit_service.turn_on_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key in ("minus", "-"):
            self.homekit_service.turn_off_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key in ("plus", "+"):
            self.homekit_service.increase_dimmer(self.selected_accessory_id)
            event.prevent_default()
        elif key in ("quotation_mark", '"'):
            self.homekit_service.decrease_dimmer(self.selected_accessory_id)
            event.prevent_default()
        elif key in ("asterisk", "star", "*"):
            self.homekit_service.levelup_selected(self.selected_accessory_id)
            event.prevent_default()
        elif key in ("cedille", "ç"):
            self.homekit_service.leveldown_selected(self.selected_accessory_id)
            event.prevent_default()

    def _select_row(self, action_key: str) -> None:
        """
        Select row in RoomListWidget by action key.

        Args:
            action_key: Action key to select.
        """
        if self.room_list_widget:
            self.room_list_widget.select_by_action_key(action_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """
        Handle row highlight changes from arrow key navigation.

        Updates selected_accessory_id when cursor moves via arrow keys.
        Skips non-accessory rows (layout rows) automatically.

        Args:
            event: Row highlighted event from DataTable.
        """
        if not self.room_list_widget or not event.row_key:
            return

        accessory_id = self.room_list_widget.get_accessory_id_for_row(event.row_key)
        if accessory_id:
            self.selected_accessory_id = accessory_id
            self._last_cursor_row = event.cursor_row
        else:
            # Non-accessory row (layout), skip to next valid row
            self._skip_to_accessory_row(event.cursor_row)

    def _skip_to_accessory_row(self, current_row: int) -> None:
        """
        Skip cursor to the nearest accessory row.

        Args:
            current_row: Current cursor row index.
        """
        if not self.room_list_widget or not self.room_list_widget.table:
            return

        table = self.room_list_widget.table
        row_count = table.row_count

        # Determine direction based on last position
        direction = 1 if current_row >= self._last_cursor_row else -1

        # Search for next accessory row in direction
        next_row = current_row + direction
        while 0 <= next_row < row_count:
            row_key = self.room_list_widget.get_row_key_at_index(next_row)
            if row_key and self.room_list_widget.get_accessory_id_for_row(row_key):
                table.move_cursor(row=next_row)
                return
            next_row += direction

        # If not found in direction, try opposite direction
        next_row = current_row - direction
        while 0 <= next_row < row_count:
            row_key = self.room_list_widget.get_row_key_at_index(next_row)
            if row_key and self.room_list_widget.get_accessory_id_for_row(row_key):
                table.move_cursor(row=next_row)
                return
            next_row -= direction

    def action_toggle_connection(self) -> None:
        """
        Toggle connection on 'c' key press.

        Connects if disconnected/failed, disconnects if connected/connecting.
        """
        self.homekit_service.toggle_connection()

    def action_refresh_all(self) -> None:
        """Refresh all module data on 'r' key press."""
        self.homekit_service.refresh_all()

    def action_toggle_selected(self) -> None:
        """Toggle selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.toggle_selected(self.selected_accessory_id)

    def action_turn_on_selected(self) -> None:
        """Turn on selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.turn_on_selected(self.selected_accessory_id)

    def action_turn_off_selected(self) -> None:
        """Turn off selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.turn_off_selected(self.selected_accessory_id)

    def action_dim_up(self) -> None:
        """Increase dimmer on selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.increase_dimmer(self.selected_accessory_id)

    def action_dim_down(self) -> None:
        """Decrease dimmer on selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.decrease_dimmer(self.selected_accessory_id)

    def action_level_up(self) -> None:
        """Increase level on selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.levelup_selected(self.selected_accessory_id)

    def action_level_down(self) -> None:
        """Decrease level on selected accessory."""
        if self.selected_accessory_id:
            self.homekit_service.leveldown_selected(self.selected_accessory_id)

    async def on_unmount(self) -> None:
        """Stop AccessoryDriver and clean up service when app unmounts."""
        await self.homekit_service.stop()
