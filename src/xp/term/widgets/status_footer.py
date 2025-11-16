"""Status Footer Widget for displaying app footer with connection status."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Static


class StatusFooterWidget(Horizontal):
    """Footer widget with connection status indicator.

    Combines the Textual Footer with a status indicator dot that shows
    the current connection state.

    Attributes:
        status_widget: Static widget displaying colored status dot.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Status Footer widget.

        Args:
            args: Additional positional arguments for Horizontal.
            kwargs: Additional keyword arguments for Horizontal.
        """
        super().__init__(*args, **kwargs)
        self.status_widget: Static = Static("○", id="status-line")

    def compose(self) -> ComposeResult:
        """Compose the footer layout.

        Yields:
            Footer and status indicator widgets.
        """
        yield Footer()
        yield self.status_widget

    def update_status(self, state: Any) -> None:
        """Update status indicator with connection state.

        Args:
            state: Current connection state (ConnectionState enum).
        """
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
