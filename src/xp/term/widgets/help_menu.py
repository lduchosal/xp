# Copyright (c) 2025 ldvchosal
"""Help Menu Widget for displaying keyboard shortcuts and protocol keys."""

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable

if TYPE_CHECKING:
    from xp.services.term.protocol_monitor_service import ProtocolMonitorService


class HelpMenuWidget(Vertical):
    """Help menu widget displaying keyboard shortcuts and protocol keys.

    Displays a table of available keyboard shortcuts mapped to their
    corresponding protocol commands.

    Attributes:
        service: ProtocolMonitorService for accessing protocol keys.
        help_table: DataTable widget for displaying key mappings.

    """

    def __init__(
        self,
        service: "ProtocolMonitorService",
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002 - mirrors Textual's Widget API
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the Help Menu widget.

        Args:
            service: ProtocolMonitorService instance.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled.

        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.service: ProtocolMonitorService = service
        self.help_table: DataTable = DataTable(
            id="help-table", show_header=False, cursor_type="row"
        )
        self.border_title = "Help menu"

    def compose(self) -> ComposeResult:
        """Compose the help menu layout.

        Yields:
            DataTable widget with key mappings.

        """
        yield self.help_table

    def on_mount(self) -> None:
        """Populate help table when widget mounts."""
        self.help_table.add_columns("Key", "Command")
        for key, config in self.service.get_keys():
            self.help_table.add_row(key, config.name)
