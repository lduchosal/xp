"""Protocol Log Widget for displaying telegram stream."""

import asyncio
import logging
from typing import Any, Optional

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog

from xp.models.term.connection_state import ConnectionState
from xp.models.term.status_message import StatusMessageChanged
from xp.models.term.telegram_display import TelegramDisplayEvent
from xp.services.term.protocol_monitor_service import ProtocolMonitorService


class ProtocolLogWidget(Widget):
    """Widget for displaying protocol telegram stream.

    Displays live RX/TX telegram stream with color-coded direction markers
    via ProtocolMonitorService.

    Attributes:
        service: ProtocolMonitorService for protocol operations.
        connection_state: Current connection state (reactive).
        logger: Logger instance for this widget.
        log_widget: RichLog widget for displaying messages.
    """

    connection_state = reactive(ConnectionState.DISCONNECTED)

    def __init__(self, service: ProtocolMonitorService) -> None:
        """Initialize the Protocol Log widget.

        Args:
            service: ProtocolMonitorService instance for protocol operations.
        """
        super().__init__()
        self.border_title = "Protocol"
        self.service = service
        self.logger = logging.getLogger(__name__)
        self.log_widget: Optional[RichLog] = None

    def compose(self) -> Any:
        """Compose the widget layout.

        Yields:
            RichLog widget for message display.
        """
        self.log_widget = RichLog(highlight=False, markup=True)
        yield self.log_widget

    async def on_mount(self) -> None:
        """Initialize connection when widget mounts.

        Delays connection by 0.5s to let UI render first.
        Connects to service signals.
        """
        # Connect to service signals
        self.service.on_connection_state_changed.connect(self._on_state_changed)
        self.service.on_telegram_display.connect(self._on_telegram_display)
        self.service.on_status_message.connect(self._on_status_message)

        # Delay connection to let UI render
        await asyncio.sleep(0.5)
        self.service.connect()

    def _on_state_changed(self, state: ConnectionState) -> None:
        """Handle connection state change from service.

        Args:
            state: New connection state.
        """
        self.connection_state = state

    def _on_telegram_display(self, event: TelegramDisplayEvent) -> None:
        """Handle telegram display event from service.

        Args:
            event: Telegram display event with direction and telegram data.
        """
        if self.log_widget:
            if event.direction == "RX":
                # Display [RX] and frame in bright green
                self.log_widget.write(f"[#00ff00]\\[RX] {event.telegram}[/#00ff00]")
            else:  # TX
                # Display [TX] and frame in bold bright green
                self.log_widget.write(
                    f"[bold #00ff00]\\[TX] {event.telegram}[/bold #00ff00]"
                )

    def _on_status_message(self, message: str) -> None:
        """Handle status message from service.

        Args:
            message: Status message to display.
        """
        self.post_status(message)

    def post_status(self, message: str) -> None:
        """Post status message.

        Args:
            message: message to be sent to status bar.
        """
        self.post_message(StatusMessageChanged(message))

    def connect(self) -> None:
        """Connect to Conbus server."""
        self.service.connect()

    def disconnect(self) -> None:
        """Disconnect from Conbus server."""
        self.service.disconnect()

    def send_telegram(self, name: str, telegram: str) -> None:
        """Send a raw telegram string.

        Args:
            name: Telegram name (e.g., "Discover")
            telegram: Telegram string (e.g., "S0000000000F01D00")
        """
        self.service.send_telegram(name, telegram)

    def clear_log(self) -> None:
        """Clear the protocol log widget."""
        if self.log_widget:
            self.log_widget.clear()
            self.post_status("Log cleared")

    def on_unmount(self) -> None:
        """Clean up when widget unmounts.

        Disconnects signals from service.
        """
        try:
            # Disconnect service signals
            self.service.on_connection_state_changed.disconnect(self._on_state_changed)
            self.service.on_telegram_display.disconnect(self._on_telegram_display)
            self.service.on_status_message.disconnect(self._on_status_message)

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
