"""Help Menu Widget for displaying keyboard shortcuts and protocol keys."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable

from xp.models.term import ProtocolKeysConfig


class HelpMenuWidget(Vertical):
    """Help menu widget displaying keyboard shortcuts and protocol keys.

    Displays a table of available keyboard shortcuts mapped to their
    corresponding protocol commands.

    Attributes:
        protocol_keys: Configuration of protocol keys and their telegrams.
        help_table: DataTable widget for displaying key mappings.
    """

    def __init__(
        self,
        protocol_keys: ProtocolKeysConfig,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the Help Menu widget.

        Args:
            protocol_keys: Configuration containing protocol key mappings.
            args: Additional positional arguments for Vertical.
            kwargs: Additional keyword arguments for Vertical.
        """
        super().__init__(*args, **kwargs)
        self.protocol_keys = protocol_keys
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
        for key, config in self.protocol_keys.protocol.items():
            self.help_table.add_row(key, config.name)
