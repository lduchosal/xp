"""Help Menu Widget for displaying keyboard shortcuts and protocol keys."""

from typing import TYPE_CHECKING, Any

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
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the Help Menu widget.

        Args:
            service: ProtocolMonitorService instance.
            args: Additional positional arguments for Vertical.
            kwargs: Additional keyword arguments for Vertical.
        """
        super().__init__(*args, **kwargs)
        self.service: ProtocolMonitorService = service
        self.help_table: DataTable = DataTable(id="help-table", show_header=False)
        self.help_table.can_focus = False
        self.border_title = "Help menu"
        self.can_focus = False

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
