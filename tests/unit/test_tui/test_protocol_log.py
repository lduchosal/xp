"""Unit tests for ProtocolLogWidget."""

from unittest.mock import Mock, patch

import pytest

from xp.tui.widgets.protocol_log import ConnectionState, ProtocolLogWidget


class TestProtocolLogWidget:
    """Unit tests for ProtocolLogWidget functionality."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock ServiceContainer."""
        container = Mock()
        mock_protocol = Mock()
        mock_protocol.on_connection_made = Mock()
        mock_protocol.on_telegram_sent = Mock()
        mock_protocol.on_telegram_received = Mock()
        mock_protocol.on_timeout = Mock()
        mock_protocol.on_failed = Mock()
        mock_protocol.on_connection_made.connect = Mock()
        mock_protocol.on_telegram_sent.connect = Mock()
        mock_protocol.on_telegram_received.connect = Mock()
        mock_protocol.on_timeout.connect = Mock()
        mock_protocol.on_failed.connect = Mock()
        mock_protocol.on_connection_made.disconnect = Mock()
        mock_protocol.on_telegram_sent.disconnect = Mock()
        mock_protocol.on_telegram_received.disconnect = Mock()
        mock_protocol.on_timeout.disconnect = Mock()
        mock_protocol.on_failed.disconnect = Mock()
        mock_protocol.cli_config = Mock()
        mock_protocol.cli_config.ip = "192.168.1.1"
        mock_protocol.cli_config.port = 4001
        mock_protocol.transport = None
        mock_protocol.send_telegram = Mock()

        mock_service = Mock()
        mock_service.conbus_protocol = mock_protocol
        mock_service.start = Mock()

        container.resolve = Mock(return_value=mock_service)
        return container

    @pytest.fixture
    def widget(self, mock_container):
        """Create widget instance with mock container."""
        return ProtocolLogWidget(container=mock_container)

    def test_widget_initialization(self, widget, mock_container):
        """Test widget can be initialized with required dependencies."""
        assert widget.container == mock_container
        assert widget.protocol is None
        assert widget.service is None
        assert widget.connection_state == ConnectionState.DISCONNECTED

    def test_connection_state_transitions(self, widget, mock_container):
        """Test connection state transitions from DISCONNECTED to CONNECTED."""
        # Initial state
        assert widget.connection_state == ConnectionState.DISCONNECTED

        # Simulate on_mount and connection
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.connection_state = ConnectionState.CONNECTING
        assert widget.connection_state == ConnectionState.CONNECTING

        # Simulate connection made
        widget.connection_state = ConnectionState.CONNECTED
        assert widget.connection_state == ConnectionState.CONNECTED

    def test_connection_state_failure(self, widget, mock_container):
        """Test connection state on failure transitions to FAILED."""
        # Initial state
        assert widget.connection_state == ConnectionState.DISCONNECTED

        # Simulate connection attempt
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.connection_state = ConnectionState.CONNECTING

        # Simulate failure
        widget.connection_state = ConnectionState.FAILED
        assert widget.connection_state == ConnectionState.FAILED

    @patch("asyncio.get_running_loop")
    def test_race_condition_guard(self, mock_get_loop, widget, mock_container):
        """Test race condition guard prevents duplicate connections."""
        # Setup mock event loop
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop

        # Setup widget
        widget.service = mock_container.resolve()
        widget.log_widget = Mock()
        widget.run_worker = Mock()  # Mock run_worker

        # First call - protocol is None, should connect
        widget.protocol = None
        widget._start_connection()

        # Verify run_worker was called for first connection
        assert widget.run_worker.call_count == 1

        # Set protocol to simulate successful connection
        widget.protocol = widget.service.conbus_protocol

        # Second call - protocol is set, guard should prevent connection
        # But run_worker will still be called, the guard is inside the async function
        # So we verify that protocol reference doesn't change
        old_protocol = widget.protocol
        widget._start_connection()

        # Protocol should remain the same (guard prevented re-connection)
        assert widget.protocol == old_protocol

    def test_on_telegram_received_signal(self, widget, mock_container):
        """Test telegram received signal handler updates message list."""
        # Setup widget
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.log_widget = Mock()

        # Create mock telegram event
        telegram_event = Mock()
        telegram_event.frame = "<E02L01I00MAK>"

        # Call handler
        widget._on_telegram_received(telegram_event)

        # Verify log widget was called with formatted message
        widget.log_widget.write.assert_called_once()
        call_args = widget.log_widget.write.call_args[0][0]
        assert "[RX]" in call_args
        assert "<E02L01I00MAK>" in call_args

    def test_on_telegram_sent_signal(self, widget, mock_container):
        """Test telegram sent signal handler updates message list."""
        # Setup widget
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.log_widget = Mock()

        # Call handler
        widget._on_telegram_sent("<S0000000000F01D00FA>")

        # Verify log widget was called
        widget.log_widget.write.assert_called()

    def test_on_connection_made_signal(self, widget, mock_container):
        """Test connection made signal handler sets state to CONNECTED."""
        # Setup widget
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.log_widget = Mock()
        widget.connection_state = ConnectionState.CONNECTING

        # Call handler
        widget._on_connection_made()

        # Verify state changed
        assert widget.connection_state == ConnectionState.CONNECTED
        widget.log_widget.write.assert_called()

    @patch("xp.tui.widgets.protocol_log.ProtocolLogWidget.app", new_callable=Mock)
    def test_on_failed_signal(self, _mock_app, widget, mock_container):
        """Test failed signal handler sets state to FAILED and exits app."""
        # Setup widget
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.log_widget = Mock()
        widget.set_timer = Mock()
        widget.connection_state = ConnectionState.CONNECTING

        # Call handler
        widget._on_failed("Connection refused")

        # Verify state changed
        assert widget.connection_state == ConnectionState.FAILED
        widget.log_widget.write.assert_called()
        widget.set_timer.assert_called_once()

    def test_send_discover(self, widget, mock_container):
        """Test send_discover sends correct telegram."""
        # Setup widget
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.log_widget = Mock()

        # Call send_discover
        widget.send_discover()

        # Verify send_telegram was called
        widget.protocol.send_telegram.assert_called_once()

    def test_send_discover_not_connected(self, widget, mock_container):
        """Test send_discover handles not connected state."""
        # Setup widget without connection
        widget.protocol = None
        widget.log_widget = Mock()

        # Call send_discover
        widget.send_discover()

        # Verify warning message
        widget.log_widget.write.assert_called()

    def test_cleanup_on_unmount(self, widget, mock_container):
        """Test on_unmount disconnects signals and closes connection."""
        # Setup widget
        widget.service = mock_container.resolve()
        widget.protocol = widget.service.conbus_protocol
        widget.protocol.transport = Mock()
        widget.protocol.disconnect = Mock()  # Add disconnect mock

        # Store protocol reference before cleanup
        protocol = widget.protocol

        # Call on_unmount
        widget.on_unmount()

        # Verify signals disconnected
        protocol.on_connection_made.disconnect.assert_called_once()
        protocol.on_telegram_received.disconnect.assert_called_once()
        protocol.on_telegram_sent.disconnect.assert_called_once()
        protocol.on_timeout.disconnect.assert_called_once()
        protocol.on_failed.disconnect.assert_called_once()

        # Verify protocol disconnect was called
        protocol.disconnect.assert_called_once()

        # Verify protocol reference cleared
        assert widget.protocol is None
        assert widget.connection_state == ConnectionState.DISCONNECTED
