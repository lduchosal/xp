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
        assert service.progress_callback is None
        assert service.finish_callback is None
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
        """Test telegram_received calls progress callback."""
        progress_mock = Mock()
        service.progress_callback = progress_mock

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
        """Test telegram_received doesn't crash when progress_callback is None."""
        service.progress_callback = None

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
        service.finish_callback = finish_mock

        service.timeout()

        assert service.receive_response.success is True
        finish_mock.assert_called_once_with(service.receive_response)

    def test_timeout_without_finish_callback(self, service):
        """Test timeout doesn't crash when finish_callback is None."""
        service.finish_callback = None

        # Should not raise any errors
        service.timeout()

    def test_failed(self, service):
        """Test failed callback updates service response."""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        service.failed("Connection timeout")

        assert service.receive_response.success is False
        assert service.receive_response.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.receive_response)

    def test_failed_without_finish_callback(self, service):
        """Test failed doesn't crash when finish_callback is None."""
        service.finish_callback = None

        # Should not raise any errors
        service.failed("Connection timeout")

    def test_start(self, service, mock_protocol):
        """Test start method sets up service parameters."""
        finish_mock = Mock()
        progress_mock = Mock()

        service.init(
            progress_callback=progress_mock,
            finish_callback=finish_mock,
            timeout_seconds=10,
        )

        assert service.progress_callback == progress_mock
        assert service.finish_callback == finish_mock
        assert mock_protocol.timeout_seconds == 10

    def test_start_without_timeout(self, service, mock_protocol):
        """Test start method with None timeout uses protocol default."""
        finish_mock = Mock()
        progress_mock = Mock()
        original_timeout = mock_protocol.timeout_seconds

        service.init(
            progress_callback=progress_mock,
            finish_callback=finish_mock,
            timeout_seconds=None,
        )

        assert service.progress_callback == progress_mock
        assert service.finish_callback == finish_mock
        # Timeout should remain unchanged
        assert mock_protocol.timeout_seconds == original_timeout

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
        finish_mock = Mock()
        progress_mock = Mock()

        # First use
        with service:
            service.init(progress_mock, finish_mock, 5.0)
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
