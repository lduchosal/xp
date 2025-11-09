"""Unit tests for ConbusEventRawService."""

from unittest.mock import Mock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.conbus.conbus_event_raw_service import ConbusEventRawService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class TestConbusEventRawService:
    """Unit tests for ConbusEventRawService functionality."""

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
        protocol._reactor = Mock()
        protocol.telegram_queue = Mock()
        protocol.call_later = Mock()
        protocol.timeout_seconds = 5
        protocol.stop_reactor = Mock()
        return protocol

    @pytest.fixture
    def service(self, mock_protocol):
        """Create service instance with mock protocol."""
        return ConbusEventRawService(conbus_protocol=mock_protocol)

    def test_service_initialization(self, service):
        """Test service can be initialized with required dependencies."""
        assert service.module_type_code == 0
        assert service.link_number == 0
        assert service.input_number == 0
        assert service.time_ms == 1000
        assert service.finish_callback is None
        assert service.progress_callback is None
        assert service.event_result.success is False

    def test_connection_made_sends_make_event(self, service, mock_protocol):
        """Test connection_made sends MAKE event telegram."""
        service.module_type_code = 2  # CP20
        service.link_number = 10
        service.input_number = 5
        service.time_ms = 1000

        service.connection_made()

        # Verify MAKE event was queued
        mock_protocol.telegram_queue.put_nowait.assert_called()
        call_args = mock_protocol.telegram_queue.put_nowait.call_args[0][0]
        assert call_args == b"E02L10I05M"

        # Verify BREAK event was scheduled
        mock_protocol.call_later.assert_called()

    def test_telegram_sent(self, service):
        """Test telegram_sent callback updates service response."""
        telegram = "<E02L10I05MAK>"

        service.telegram_sent(telegram)

        assert service.event_result.sent_telegrams == [telegram]

    def test_telegram_received(self, service, mock_protocol):
        """Test telegram_received callback updates service response."""
        telegram_event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<E02L10I05MAK>",
            telegram="E02L10I05MAK",
            payload="E02L10I05M",
            telegram_type="E",
            serial_number="",
            checksum="AK",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        assert service.event_result.received_telegrams == ["<E02L10I05MAK>"]

    def test_telegram_received_with_progress_callback(self, service, mock_protocol):
        """Test telegram_received calls progress callback."""
        progress_mock = Mock()
        service.progress_callback = progress_mock

        telegram_event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<E02L10I05MAK>",
            telegram="E02L10I05MAK",
            payload="E02L10I05M",
            telegram_type="E",
            serial_number="",
            checksum="AK",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        progress_mock.assert_called_once_with("<E02L10I05MAK>")

    def test_timeout(self, service, mock_protocol):
        """Test timeout callback marks operation as successful."""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        service.timeout()

        assert service.event_result.success is True
        assert service.event_result.error is None
        finish_mock.assert_called_once_with(service.event_result)
        mock_protocol.stop_reactor.assert_called_once()

    def test_failed(self, service, mock_protocol):
        """Test failed callback updates service response."""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        service.failed("Connection timeout")

        assert service.event_result.success is False
        assert service.event_result.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.event_result)
        mock_protocol.stop_reactor.assert_called_once()

    def test_run(self, service, mock_protocol):
        """Test run method sets up service parameters."""
        finish_mock = Mock()
        progress_mock = Mock()

        service.run(
            module_type_code=33,  # XP33
            link_number=15,
            input_number=8,
            time_ms=500,
            progress_callback=progress_mock,
            finish_callback=finish_mock,
            timeout_seconds=10,
        )

        assert service.module_type_code == 33
        assert service.link_number == 15
        assert service.input_number == 8
        assert service.time_ms == 500
        assert service.progress_callback == progress_mock
        assert service.finish_callback == finish_mock
        assert mock_protocol.timeout_seconds == 10

    def test_send_break_event(self, service, mock_protocol):
        """Test _send_break_event sends BREAK event telegram."""
        service.module_type_code = 2  # CP20
        service.link_number = 10
        service.input_number = 5

        service._send_break_event()

        # Verify BREAK event was queued
        mock_protocol.telegram_queue.put_nowait.assert_called()
        call_args = mock_protocol.telegram_queue.put_nowait.call_args[0][0]
        assert call_args == b"E02L10I05B"
