"""Room List Widget for displaying HomeKit accessories table."""

from datetime import datetime
from typing import Any, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from xp.models.term.accessory_state import AccessoryState
from xp.services.term.homekit_service import HomekitService


class RoomListWidget(Static):
    """
    Widget displaying HomeKit accessories in a data table.

    Shows room/accessory hierarchy with real-time state updates from HomekitService.
    Table displays: room/accessory, action, state, dim, module, serial, type, status, output, updated.

    Attributes:
        service: HomekitService for accessory state updates.
        table: DataTable widget displaying accessory information.
    """

    def __init__(
        self,
        service: Optional[HomekitService] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Room List widget.

        Args:
            service: Optional HomekitService for signal subscriptions.
            args: Additional positional arguments for Static.
            kwargs: Additional keyword arguments for Static.
        """
        super().__init__(*args, **kwargs)
        self.service = service
        self.table: Optional[DataTable] = None
        self._row_keys: dict[str, Any] = {}  # Map accessory_id to row key
        self._row_to_accessory: dict[Any, str] = {}  # Map row key to accessory_id
        self._row_index_to_key: list[Any] = []  # Map row index to row key
        self._action_to_row: dict[str, Any] = {}  # Map action key to row key
        self._current_room: str = ""

    def compose(self) -> ComposeResult:
        """
        Compose the widget layout.

        Yields:
            DataTable widget.
        """
        self.table = DataTable(id="rooms-table", cursor_type="row")
        yield self.table

    def on_mount(self) -> None:
        """Initialize table and subscribe to service signals when widget mounts."""
        self.border_title = "Rooms"

        if self.table:
            self.table.add_column("room / accessory", key="name", width=35)
            self.table.add_column("action", key="action", width=8)
            self.table.add_column("state", key="state", width=7)
            self.table.add_column("dim", key="dim", width=6)
            self.table.add_column("module", key="module", width=8)
            self.table.add_column("serial", key="serial", width=12)
            self.table.add_column("type", key="type", width=10)
            self.table.add_column("status", key="status", width=8)
            self.table.add_column("output", key="output", width=7)
            self.table.add_column("updated", key="updated", width=10)

        if self.service:
            self.service.on_room_list_updated.connect(self.update_accessory_list)
            self.service.on_module_state_changed.connect(self.update_accessory_state)

    def on_unmount(self) -> None:
        """Unsubscribe from service signals when widget unmounts."""
        if self.service:
            self.service.on_room_list_updated.disconnect(self.update_accessory_list)
            self.service.on_module_state_changed.disconnect(self.update_accessory_state)

    def update_accessory_list(self, accessory_states: List[AccessoryState]) -> None:
        """
        Update entire accessory list from service.

        Clears existing table and repopulates with all accessories grouped by room.

        Args:
            accessory_states: List of all accessory states.
        """
        if not self.table:
            return

        self.table.clear()
        self._row_keys.clear()
        self._row_to_accessory.clear()
        self._row_index_to_key.clear()
        self._action_to_row.clear()
        self._current_room = ""

        for state in accessory_states:
            # Add room header row if new room
            if state.room_name != self._current_room:
                self._current_room = state.room_name
                # Add layout rows (empty and header) - not selectable
                self._row_index_to_key.extend(
                    [
                        self.table.add_row(),
                        self.table.add_row(Text(state.room_name, style="bold")),
                        self.table.add_row(),
                    ]
                )

            self._add_accessory_row(state)

    def update_accessory_state(self, state: AccessoryState) -> None:
        """
        Update individual accessory state in table.

        Updates existing row if accessory exists, otherwise adds new row.

        Args:
            state: Updated accessory state.
        """
        if not self.table:
            return

        accessory_id = f"{state.module_name}_{state.output}"

        if accessory_id in self._row_keys:
            row_key = self._row_keys[accessory_id]
            self.table.update_cell(
                row_key, "state", Text(state.output_state, justify="center")
            )
            self.table.update_cell(
                row_key, "dim", Text(self._format_dim(state), justify="center")
            )
            self.table.update_cell(row_key, "status", state.error_status)
            self.table.update_cell(
                row_key,
                "updated",
                Text(self._format_last_update(state.last_update), justify="center"),
            )
        else:
            self._add_accessory_row(state)

    def _add_accessory_row(self, state: AccessoryState) -> None:
        """
        Add an accessory row to the table.

        Args:
            state: Accessory state to add.
        """
        if not self.table:
            return

        accessory_id = f"{state.module_name}_{state.output}"
        row_key = self.table.add_row(
            f"  - {state.accessory_name}",
            Text(state.action, justify="center"),
            Text(state.output_state, justify="center"),
            Text(self._format_dim(state), justify="center"),
            state.module_name,
            state.serial_number,
            state.module_type,
            state.error_status,
            Text(str(state.output), justify="right"),
            Text(self._format_last_update(state.last_update), justify="center"),
        )
        self._row_keys[accessory_id] = row_key
        self._row_to_accessory[row_key] = accessory_id
        self._row_index_to_key.append(row_key)
        if state.action:
            self._action_to_row[state.action] = row_key

    def _format_dim(self, state: AccessoryState) -> str:
        """
        Format dimming state for display.

        Shows percentage if dimmable and ON, "-" if dimmable and OFF, empty otherwise.

        Args:
            state: Accessory state.

        Returns:
            Formatted dimming string.
        """
        if not state.is_dimmable():
            return ""
        if state.output_state == "OFF":
            return "-"
        return state.dimming_state or ""

    def _format_last_update(self, last_update: Optional[datetime]) -> str:
        """
        Format last update timestamp for display.

        Shows elapsed time in HH:MM:SS format or "--:--:--" if never updated.

        Args:
            last_update: Last update timestamp or None.

        Returns:
            Formatted time string.
        """
        if last_update is None:
            return "--:--:--"

        elapsed = datetime.now() - last_update
        total_seconds = int(elapsed.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def refresh_last_update_times(self) -> None:
        """
        Refresh only the last_update column for all accessories.

        Updates the elapsed time display without querying the service.
        """
        if not self.table or not self.service:
            return

        for accessory_id, row_key in self._row_keys.items():
            state = next(
                (
                    s
                    for s in self.service.accessory_states
                    if f"{s.module_name}_{s.output}" == accessory_id
                ),
                None,
            )
            if state:
                self.table.update_cell(
                    row_key,
                    "updated",
                    Text(
                        self._format_last_update(state.last_update),
                        justify="center",
                    ),
                )

    def select_by_action_key(self, action_key: str) -> None:
        """
        Select and highlight row by action key.

        Moves the table cursor to the row corresponding to the action key.

        Args:
            action_key: Action key (a-z0-9) to select.
        """
        if not self.table:
            return

        row_key = self._action_to_row.get(action_key)
        if row_key is not None:
            row_index = self.table.get_row_index(row_key)
            self.table.move_cursor(row=row_index)

    def get_accessory_id_for_row(self, row_key: Any) -> Optional[str]:
        """
        Get accessory ID for a row key.

        Args:
            row_key: DataTable row key.

        Returns:
            Accessory ID if found, None otherwise.
        """
        return self._row_to_accessory.get(row_key)

    def get_row_key_at_index(self, index: int) -> Optional[Any]:
        """
        Get row key at a given index.

        Args:
            index: Row index.

        Returns:
            Row key if valid index, None otherwise.
        """
        if 0 <= index < len(self._row_index_to_key):
            return self._row_index_to_key[index]
        return None
