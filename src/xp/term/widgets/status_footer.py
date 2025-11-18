"""Status Footer Widget for displaying app footer with connection status."""

from typing import Any, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Static

from xp.models.term.connection_state import ConnectionState
from xp.services.term.protocol_monitor_service import ProtocolMonitorService


class StatusFooterWidget(Horizontal):
    """Footer widget with connection status indicator.

    Combines the Textual Footer with a status indicator dot that shows
    the current connection state. Subscribes directly to service signals.

    Attributes:
        service: ProtocolMonitorService for connection state and status updates.
        status_widget: Static widget displaying colored status dot.
        status_text_widget: Static widget displaying status messages.
    """

    def __init__(
        self,
        service: Optional[ProtocolMonitorService] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the Status Footer widget.

        Args:
            service: Optional ProtocolMonitorService for signal subscriptions.
            args: Additional positional arguments for Horizontal.
            kwargs: Additional keyword arguments for Horizontal.
        """
        super().__init__(*args, **kwargs)
        self.service = service
        self.status_text_widget: Static = Static("", id="status-text")
        self.status_widget: Static = Static("○", id="status-line")

    def compose(self) -> ComposeResult:
        """Compose the footer layout.

        Yields:
            Footer and status indicator widgets.
        """
        yield Footer()
        yield self.status_text_widget
        yield self.status_widget

    def on_mount(self) -> None:
        """Subscribe to service signals when widget mounts."""
        if self.service:
            self.service.on_connection_state_changed.connect(self.update_status)
            self.service.on_status_message.connect(self.update_message)

    def on_unmount(self) -> None:
        """Unsubscribe from service signals when widget unmounts."""
        if self.service:
            self.service.on_connection_state_changed.disconnect(self.update_status)
            self.service.on_status_message.disconnect(self.update_message)

    def update_status(self, state: ConnectionState) -> None:
        """Update status indicator with connection state.

        Args:
            state: Current connection state (ConnectionState enum).
        """
        # Map states to colored dots
        dot = {
            "CONNECTED": "[green]●[/green]",
            "CONNECTING": "[yellow]●[/yellow]",
            "DISCONNECTING": "[yellow]●[/yellow]",
            "FAILED": "[red]●[/red]",
            "DISCONNECTED": "○",
        }.get(state.value, "○")
        self.status_widget.update(dot)

    def update_message(self, message: str) -> None:
        """Update status text with message.

        Args:
            message: Status message to display.
        """
        self.status_text_widget.update(message)
