"""Unit tests for ProtocolLogWidget."""

from unittest.mock import Mock

import pytest

from xp.models.term.telegram_display import TelegramDisplayEvent
from xp.term.widgets.protocol_log import ProtocolLogWidget


class TestProtocolLogWidget:
    """Unit tests for ProtocolLogWidget functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock ProtocolMonitorService."""
        service = Mock()
        service.on_telegram_display = Mock()
        service.on_telegram_display.connect = Mock()
        service.on_telegram_display.disconnect = Mock()
        service.connect = Mock()
        service.disconnect = Mock()
        service.send_telegram = Mock()
        return service

    @pytest.fixture
    def widget(self, mock_service):
        """Create widget instance with mock service."""
        return ProtocolLogWidget(service=mock_service)

    def test_widget_initialization(self, widget, mock_service):
        """Test widget can be initialized with required dependencies."""
        assert widget.service == mock_service

    def test_on_telegram_display_rx(self, widget):
        """Test telegram display handler for RX telegrams."""
        widget.log_widget = Mock()

        # Create RX telegram event
        event = TelegramDisplayEvent(direction="RX", telegram="<E02L01I00MAK>")

        # Call handler
        widget._on_telegram_display(event)

        # Verify log widget was called with formatted message
        widget.log_widget.write.assert_called_once()
        call_args = widget.log_widget.write.call_args[0][0]
        assert "[RX]" in call_args
        assert "<E02L01I00MAK>" in call_args

    def test_on_telegram_display_tx(self, widget):
        """Test telegram display handler for TX telegrams."""
        widget.log_widget = Mock()

        # Create TX telegram event
        event = TelegramDisplayEvent(direction="TX", telegram="<S0000000000F01D00FA>")

        # Call handler
        widget._on_telegram_display(event)

        # Verify log widget was called with formatted message
        widget.log_widget.write.assert_called_once()
        call_args = widget.log_widget.write.call_args[0][0]
        assert "[TX]" in call_args
        assert "<S0000000000F01D00FA>" in call_args

    def test_clear_log(self, widget):
        """Test clear_log clears the log widget."""
        widget.log_widget = Mock()

        widget.clear_log()

        widget.log_widget.clear.assert_called_once()

    def test_cleanup_on_unmount(self, widget, mock_service):
        """Test on_unmount disconnects signals from service."""
        # Call on_unmount
        widget.on_unmount()

        # Verify signals disconnected
        mock_service.on_telegram_display.disconnect.assert_called_once()
