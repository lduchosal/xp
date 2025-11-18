"""Unit tests for ProtocolLogWidget."""

from unittest.mock import Mock

import pytest

from xp.models.term.telegram_display import TelegramDisplayEvent
from xp.term.widgets.protocol_log import ConnectionState, ProtocolLogWidget


class TestProtocolLogWidget:
    """Unit tests for ProtocolLogWidget functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock ProtocolMonitorService."""
        service = Mock()
        service.connection_state = ConnectionState.DISCONNECTED
        service.server_info = "192.168.1.1:4001"
        service.on_connection_state_changed = Mock()
        service.on_telegram_display = Mock()
        service.on_status_message = Mock()
        service.on_connection_state_changed.connect = Mock()
        service.on_telegram_display.connect = Mock()
        service.on_status_message.connect = Mock()
        service.on_connection_state_changed.disconnect = Mock()
        service.on_telegram_display.disconnect = Mock()
        service.on_status_message.disconnect = Mock()
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
        assert widget.connection_state == ConnectionState.DISCONNECTED

    def test_connection_state_transitions(self, widget):
        """Test connection state transitions from DISCONNECTED to CONNECTED."""
        # Initial state
        assert widget.connection_state == ConnectionState.DISCONNECTED

        # Simulate state change
        widget.connection_state = ConnectionState.CONNECTING
        assert widget.connection_state == ConnectionState.CONNECTING

        # Simulate connection made
        widget.connection_state = ConnectionState.CONNECTED
        assert widget.connection_state == ConnectionState.CONNECTED

    def test_connection_state_failure(self, widget):
        """Test connection state on failure transitions to FAILED."""
        # Initial state
        assert widget.connection_state == ConnectionState.DISCONNECTED

        # Simulate connection attempt
        widget.connection_state = ConnectionState.CONNECTING

        # Simulate failure
        widget.connection_state = ConnectionState.FAILED
        assert widget.connection_state == ConnectionState.FAILED

    def test_on_state_changed_handler(self, widget):
        """Test state changed handler updates widget state."""
        widget._on_state_changed(ConnectionState.CONNECTED)
        assert widget.connection_state == ConnectionState.CONNECTED

        widget._on_state_changed(ConnectionState.FAILED)
        assert widget.connection_state == ConnectionState.FAILED

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

    def test_on_status_message(self, widget):
        """Test status message handler posts message."""
        widget.post_status = Mock()

        # Call handler
        widget._on_status_message("Test message")

        # Verify post_status was called
        widget.post_status.assert_called_once_with("Test message")

    def test_connect_delegates_to_service(self, widget, mock_service):
        """Test connect method delegates to service."""
        widget.connect()
        mock_service.connect.assert_called_once()

    def test_disconnect_delegates_to_service(self, widget, mock_service):
        """Test disconnect method delegates to service."""
        widget.disconnect()
        mock_service.disconnect.assert_called_once()

    def test_send_telegram_delegates_to_service(self, widget, mock_service):
        """Test send_telegram delegates to service."""
        widget.send_telegram("Discover", "S0000000000F01D00")
        mock_service.send_telegram.assert_called_once_with(
            "Discover", "S0000000000F01D00"
        )

    def test_clear_log(self, widget):
        """Test clear_log clears the log widget."""
        widget.log_widget = Mock()
        widget.post_status = Mock()

        widget.clear_log()

        widget.log_widget.clear.assert_called_once()
        widget.post_status.assert_called_once_with("Log cleared")

    def test_cleanup_on_unmount(self, widget, mock_service):
        """Test on_unmount disconnects signals from service."""
        # Call on_unmount
        widget.on_unmount()

        # Verify signals disconnected
        mock_service.on_connection_state_changed.disconnect.assert_called_once()
        mock_service.on_telegram_display.disconnect.assert_called_once()
        mock_service.on_status_message.disconnect.assert_called_once()
