"""Protocol Log Widget for displaying telegram stream."""

import logging
from typing import Any, Optional

from textual.widget import Widget
from textual.widgets import RichLog

from xp.models.term.telegram_display import TelegramDisplayEvent
from xp.services.term.protocol_monitor_service import ProtocolMonitorService


class ProtocolLogWidget(Widget):
    """Widget for displaying protocol telegram stream.

    Displays live RX/TX telegram stream with color-coded direction markers
    via ProtocolMonitorService.

    Attributes:
        service: ProtocolMonitorService for protocol operations.
        logger: Logger instance for this widget.
        log_widget: RichLog widget for displaying messages.
    """

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

    def on_mount(self) -> None:
        """Initialize widget when mounted.

        Connects to service signals for telegram display.
        """
        # Connect to service signals
        self.service.on_telegram_display.connect(self._on_telegram_display)

    def _on_telegram_display(self, event: TelegramDisplayEvent) -> None:
        """Handle telegram display event from service.

        Args:
            event: Telegram display event with direction and telegram data.
        """
        if self.log_widget:
            color = "bold #00ff00" if event.direction == "TX" else "#00ff00"
            self.log_widget.write(
                f"[{color}]\\[{event.direction}] {event.telegram}[/{color}]"
            )

    def clear_log(self) -> None:
        """Clear the protocol log widget."""
        if self.log_widget:
            self.log_widget.clear()

    def on_unmount(self) -> None:
        """Clean up when widget unmounts.

        Disconnects signals from service.
        """
        try:
            # Disconnect service signals
            self.service.on_telegram_display.disconnect(self._on_telegram_display)

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
