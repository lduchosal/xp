"""Unit tests for ConbusReceiveService."""

from unittest.mock import Mock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.conbus.conbus_receive_service import ConbusReceiveService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class TestConbusReceiveService:
    """Unit tests for ConbusReceiveService functionality."""

    @pytest.fixture
    def mock_protocol(self):
        """Create a mock ConbusEventProtocol."""
        protocol = Mock(spec=ConbusEventProtocol)
        protocol.on_connection_made = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_timeout = Mock()
        protocol.on_failed = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed.disconnect = Mock()
        protocol.timeout_seconds = 5
        protocol.start_reactor = Mock()
        protocol.stop_reactor = Mock()
        return protocol

    @pytest.fixture
    def service(self, mock_protocol):
        """Create service instance with mock protocol."""
        return ConbusReceiveService(conbus_protocol=mock_protocol)

    def test_service_initialization(self, service, mock_protocol):
        """Test service can be initialized with required dependencies."""
        assert service.receive_response.success is True
        assert service.receive_response.received_telegrams == []

        # Verify signal connections
        mock_protocol.on_connection_made.connect.assert_called_once()
        mock_protocol.on_telegram_sent.connect.assert_called_once()
        mock_protocol.on_telegram_received.connect.assert_called_once()
        mock_protocol.on_timeout.connect.assert_called_once()
        mock_protocol.on_failed.connect.assert_called_once()

    def test_connection_made(self, service):
        """Test connection_made logs correctly."""
        # Should not raise any errors
        service.connection_made()

    def test_telegram_sent(self, service):
        """Test telegram_sent callback (no-op for receive service)."""
        telegram = "<T123456789012D0AK>"

        # Should not raise any errors
        service.telegram_sent(telegram)

    def test_telegram_received(self, service, mock_protocol):
        """Test telegram_received callback updates service response."""
        telegram_event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<T123456789012D0AK>",
            telegram="T123456789012D0AK",
            payload="T123456789012D0",
            telegram_type="T",
            serial_number="1234567890",
            checksum="AK",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        assert service.receive_response.received_telegrams == ["<T123456789012D0AK>"]

    def test_telegram_received_multiple(self, service, mock_protocol):
        """Test telegram_received appends to received_telegrams list."""
        telegram_event_1 = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<T123456789012D0AK>",
            telegram="T123456789012D0AK",
            payload="T123456789012D0",
            telegram_type="T",
            serial_number="1234567890",
            checksum="AK",
            checksum_valid=True,
        )

        telegram_event_2 = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<T987654321098D1AK>",
            telegram="T987654321098D1AK",
            payload="T987654321098D1",
            telegram_type="T",
            serial_number="9876543210",
            checksum="AK",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event_1)
        service.telegram_received(telegram_event_2)

        assert service.receive_response.received_telegrams == [
            "<T123456789012D0AK>",
            "<T987654321098D1AK>",
        ]

    def test_telegram_received_with_progress_callback(self, service, mock_protocol):
        """Test telegram_received emits progress signal."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        telegram_event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<T123456789012D0AK>",
            telegram="T123456789012D0AK",
            payload="T123456789012D0",
            telegram_type="T",
            serial_number="1234567890",
            checksum="AK",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        progress_mock.assert_called_once_with("<T123456789012D0AK>")

    def test_telegram_received_without_progress_callback(self, service, mock_protocol):
        """Test telegram_received doesn't crash when no signal handlers connected."""
        telegram_event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<T123456789012D0AK>",
            telegram="T123456789012D0AK",
            payload="T123456789012D0",
            telegram_type="T",
            serial_number="1234567890",
            checksum="AK",
            checksum_valid=True,
        )

        # Should not raise any errors
        service.telegram_received(telegram_event)

    def test_timeout(self, service, mock_protocol):
        """Test timeout callback marks operation as successful."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        assert service.receive_response.success is True
        finish_mock.assert_called_once_with(service.receive_response)

    def test_timeout_without_finish_callback(self, service):
        """Test timeout doesn't crash when no signal handlers connected."""
        # Should not raise any errors
        service.timeout()

    def test_failed(self, service):
        """Test failed callback updates service response."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection timeout")

        assert service.receive_response.success is False
        assert service.receive_response.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.receive_response)

    def test_failed_without_finish_callback(self, service):
        """Test failed doesn't crash when no signal handlers connected."""
        # Should not raise any errors
        service.failed("Connection timeout")

    def test_set_timeout(self, service, mock_protocol):
        """Test set_timeout method sets timeout on protocol."""
        service.set_timeout(timeout_seconds=10)

        assert mock_protocol.timeout_seconds == 10

    def test_signal_connections(self, service):
        """Test signals can be connected and emit correctly."""
        finish_mock = Mock()
        progress_mock = Mock()

        # Connect signals
        service.on_progress.connect(progress_mock)
        service.on_finish.connect(finish_mock)

        # Emit signals
        service.on_progress.emit("test_telegram")
        service.on_finish.emit(service.receive_response)

        # Verify callbacks were called
        progress_mock.assert_called_once_with("test_telegram")
        finish_mock.assert_called_once_with(service.receive_response)

    def test_start_reactor(self, service, mock_protocol):
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_protocol.start_reactor.assert_called_once()

    def test_context_manager_enter(self, service):
        """Test __enter__ resets state and returns self."""
        # Modify state
        service.receive_response.success = False
        service.receive_response.error = "Some error"
        service.receive_response.received_telegrams = ["<T123456789012D0AK>"]

        # Enter context
        result = service.__enter__()

        # Verify state reset
        assert result is service
        assert service.receive_response.success is True
        assert service.receive_response.error is None
        assert service.receive_response.received_telegrams == []

    def test_context_manager_exit(self, service, mock_protocol):
        """Test __exit__ disconnects all signals."""
        service.__exit__(None, None, None)

        # Verify all signals disconnected
        mock_protocol.on_connection_made.disconnect.assert_called_once()
        mock_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_protocol.on_timeout.disconnect.assert_called_once()
        mock_protocol.on_failed.disconnect.assert_called_once()

    def test_context_manager_full_lifecycle(self, service, mock_protocol):
        """Test full context manager lifecycle with singleton reuse."""
        # First use
        with service:
            # Simulate receiving a telegram
            service.receive_response.received_telegrams = ["<T123456789012D0AK>"]

        # Verify signals disconnected after first use
        assert mock_protocol.on_connection_made.disconnect.call_count == 1

        # Second use (singleton reuse)
        mock_protocol.on_connection_made.connect.reset_mock()
        mock_protocol.on_connection_made.disconnect.reset_mock()

        # Note: In real usage, signals would be reconnected in __init__
        # but since we're reusing the same instance in tests, we need to
        # manually reconnect or create a new instance
        service2 = ConbusReceiveService(conbus_protocol=mock_protocol)

        with service2:
            # Verify state was reset
            assert service2.receive_response.received_telegrams == []
            assert service2.receive_response.success is True
