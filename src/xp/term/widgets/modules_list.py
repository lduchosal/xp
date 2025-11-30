"""Modules List Widget for displaying module state table."""

from datetime import datetime
from typing import Any, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from xp.models.term.module_state import ModuleState
from xp.services.term.state_monitor_service import StateMonitorService


class ModulesListWidget(Static):
    """
    Widget displaying module states in a data table.

    Shows module information with real-time updates from StateMonitorService.
    Table displays: name, serial_number, module_type, link_number, outputs, report, status, last_update.

    Attributes:
        service: StateMonitorService for module state updates.
        table: DataTable widget displaying module information.
    """

    def __init__(
        self,
        service: Optional[StateMonitorService] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Modules List widget.

        Args:
            service: Optional StateMonitorService for signal subscriptions.
            args: Additional positional arguments for Static.
            kwargs: Additional keyword arguments for Static.
        """
        super().__init__(*args, **kwargs)
        self.service = service
        self.table: Optional[DataTable] = None
        self._row_keys: dict[str, Any] = {}  # Map serial_number to row key

    def compose(self) -> ComposeResult:
        """
        Compose the widget layout.

        Yields:
            DataTable widget.
        """
        self.table = DataTable(id="modules-table", cursor_type="row")
        yield self.table

    def on_mount(self) -> None:
        """Initialize table and subscribe to service signals when widget mounts."""
        # Set border title
        self.border_title = "Modules"

        if self.table:
            # Setup table columns
            self.table.add_column("name", key="name")
            self.table.add_column("link", key="link_number")
            self.table.add_column("serial number", key="serial_number")
            self.table.add_column("module type", key="module_type")
            self.table.add_column("outputs", key="outputs")
            self.table.add_column("report", key="report")
            self.table.add_column("status", key="status")
            self.table.add_column("last update", key="last_update")

        if self.service:
            self.service.on_module_list_updated.connect(self.update_module_list)
            self.service.on_module_state_changed.connect(self.update_module_state)

    def on_unmount(self) -> None:
        """Unsubscribe from service signals when widget unmounts."""
        if self.service:
            self.service.on_module_list_updated.disconnect(self.update_module_list)
            self.service.on_module_state_changed.disconnect(self.update_module_state)

    def update_module_list(self, module_states: List[ModuleState]) -> None:
        """
        Update entire module list from service.

        Clears existing table and repopulates with all modules.

        Args:
            module_states: List of all module states.
        """
        if not self.table:
            return

        # Clear existing rows
        self.table.clear()
        self._row_keys.clear()

        # Add all modules
        for module_state in module_states:
            self._add_module_row(module_state)

    def update_module_state(self, module_state: ModuleState) -> None:
        """
        Update individual module state in table.

        Updates existing row if module exists, otherwise adds new row.

        Args:
            module_state: Updated module state.
        """
        if not self.table:
            return

        serial_number = module_state.serial_number

        if serial_number in self._row_keys:
            # Update existing row
            row_key = self._row_keys[serial_number]
            self.table.update_cell(
                row_key,
                "outputs",
                Text(self._format_outputs(module_state.outputs), justify="right"),
            )
            self.table.update_cell(
                row_key,
                "report",
                Text(self._format_report(module_state.auto_report), justify="center"),
            )
            self.table.update_cell(row_key, "status", module_state.error_status)
            self.table.update_cell(
                row_key,
                "last_update",
                Text(
                    self._format_last_update(module_state.last_update), justify="center"
                ),
            )
        else:
            # Add new row
            self._add_module_row(module_state)

    def _add_module_row(self, module_state: ModuleState) -> None:
        """
        Add a module row to the table.

        Args:
            module_state: Module state to add.
        """
        if not self.table:
            return

        row_key = self.table.add_row(
            module_state.name,
            Text(str(module_state.link_number), justify="right"),
            module_state.serial_number,
            module_state.module_type,
            Text(self._format_outputs(module_state.outputs), justify="right"),
            Text(self._format_report(module_state.auto_report), justify="center"),
            module_state.error_status,
            Text(self._format_last_update(module_state.last_update), justify="center"),
        )
        self._row_keys[module_state.serial_number] = row_key

    def _format_outputs(self, outputs: str) -> str:
        """
        Format outputs for display.

        Args:
            outputs: Raw output string.

        Returns:
            Formatted output string (empty string for modules without outputs).
        """
        return outputs

    def _format_report(self, auto_report: bool) -> str:
        """
        Format auto-report status for display.

        Args:
            auto_report: Auto-report boolean value.

        Returns:
            "Y" if True, "N" if False.
        """
        return "Y" if auto_report else "N"

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

        # Calculate elapsed time
        elapsed = datetime.now() - last_update
        total_seconds = int(elapsed.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def refresh_last_update_times(self) -> None:
        """
        Refresh only the last_update column for all modules.

        Updates the elapsed time display without querying the service.
        """
        if not self.table or not self.service:
            return

        # Update last_update column for each module
        for serial_number, row_key in self._row_keys.items():
            # Get the module state from service
            module_states = self.service.module_states
            module_state = next(
                (m for m in module_states if m.serial_number == serial_number), None
            )
            if module_state:
                # Update only the last_update cell
                self.table.update_cell(
                    row_key,
                    "last_update",
                    Text(
                        self._format_last_update(module_state.last_update),
                        justify="center",
                    ),
                )
