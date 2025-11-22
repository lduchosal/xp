"""Unit tests for ConbusRawService."""

from unittest.mock import Mock

import pytest

from xp.services.conbus.conbus_raw_service import ConbusRawService


class TestConbusRawService:
    """Unit tests for ConbusRawService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create a mock ConbusEventProtocol."""
        protocol = Mock()
        protocol.timeout_seconds = 5.0
        # Mock signals
        protocol.on_connection_made = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_timeout = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_failed = Mock()
        protocol.on_failed.connect = Mock()
        return protocol

    @pytest.fixture
    def service(self, mock_conbus_protocol):
        """Create service instance with test protocol."""
        return ConbusRawService(
            conbus_protocol=mock_conbus_protocol,
        )

    def test_service_initialization(self, service, mock_conbus_protocol):
        """Test service can be initialized with required dependencies."""
        assert service.raw_input == ""
        assert service.service_response.success is False
        # Verify signals were connected
        assert mock_conbus_protocol.on_connection_made.connect.called
        assert mock_conbus_protocol.on_telegram_sent.connect.called
        assert mock_conbus_protocol.on_telegram_received.connect.called
        assert mock_conbus_protocol.on_timeout.connect.called
        assert mock_conbus_protocol.on_failed.connect.called

    def test_service_context_manager(self, service):
        """Test service can be used as context manager."""
        with service as s:
            assert s is service

    def test_telegram_sent(self, service):
        """Test telegram_sent callback updates service response."""
        telegram = "<S2113010000F02D12>"
        service.telegram_sent(telegram)

        assert service.service_response.success is True
        assert service.service_response.sent_telegrams == telegram
        assert service.service_response.received_telegrams == []

    def test_telegram_received(self, service, mock_conbus_protocol):
        """Test telegram_received callback updates service response."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame="<R2113010000F02D12>",
            telegram="R2113010000F02D12",
            payload="R2113010000F02D",
            telegram_type="R",
            serial_number="2113010000",
            checksum="12",
            checksum_valid=True,
        )
        service.telegram_received(telegram_event)

        assert service.service_response.received_telegrams == ["<R2113010000F02D12>"]

    def test_telegram_received_multiple(self, service, mock_conbus_protocol):
        """Test multiple telegram_received callbacks."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        telegram1 = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame="<R2113010000F02D12>",
            telegram="R2113010000F02D12",
            payload="R2113010000F02D",
            telegram_type="R",
            serial_number="2113010000",
            checksum="12",
            checksum_valid=True,
        )
        telegram2 = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame="<R2113010001F02D12>",
            telegram="R2113010001F02D12",
            payload="R2113010001F02D",
            telegram_type="R",
            serial_number="2113010001",
            checksum="12",
            checksum_valid=True,
        )

        service.telegram_received(telegram1)
        service.telegram_received(telegram2)

        assert len(service.service_response.received_telegrams) == 2
        assert service.service_response.received_telegrams[0] == "<R2113010000F02D12>"
        assert service.service_response.received_telegrams[1] == "<R2113010001F02D12>"

    def test_telegram_received_emits_progress_signal(
        self, service, mock_conbus_protocol
    ):
        """Test telegram_received emits progress signal."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame="<R2113010000F02D12>",
            telegram="R2113010000F02D12",
            payload="R2113010000F02D",
            telegram_type="R",
            serial_number="2113010000",
            checksum="12",
            checksum_valid=True,
        )
        service.telegram_received(telegram_event)

        progress_mock.assert_called_once_with("<R2113010000F02D12>")

    def test_timeout(self, service):
        """Test timeout emits finish signal."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        result = service.timeout()

        assert result is None
        finish_mock.assert_called_once_with(service.service_response)

    def test_failed(self, service):
        """Test failed updates service response and emits finish signal."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection failed")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection failed"
        finish_mock.assert_called_once_with(service.service_response)

    def test_set_timeout(self, service, mock_conbus_protocol):
        """Test set_timeout delegates to protocol."""
        service.set_timeout(10.0)
        assert mock_conbus_protocol.timeout_seconds == 10.0

    def test_start_reactor(self, service, mock_conbus_protocol):
        """Test start_reactor delegates to protocol."""
        service.start_reactor()
        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(self, service, mock_conbus_protocol):
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_context_manager_enter_resets_state(self, service):
        """Test __enter__ resets state for singleton reuse."""
        # Set some state
        service.raw_input = "test"
        service.service_response.success = True

        # Enter context
        result = service.__enter__()

        # Verify state is reset
        assert result is service
        assert service.raw_input == ""
        assert service.service_response.success is False

    def test_context_manager_exit_disconnects_signals(
        self, service, mock_conbus_protocol
    ):
        """Test __exit__ disconnects all signals and stops reactor."""
        # Setup signal mocks with disconnect method
        mock_conbus_protocol.on_connection_made.disconnect = Mock()
        mock_conbus_protocol.on_telegram_sent.disconnect = Mock()
        mock_conbus_protocol.on_telegram_received.disconnect = Mock()
        mock_conbus_protocol.on_timeout.disconnect = Mock()
        mock_conbus_protocol.on_failed.disconnect = Mock()

        # Exit context
        service.__exit__(None, None, None)

        # Verify protocol signals were disconnected
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()

        # Verify reactor was stopped
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_connection_made(self, service, mock_conbus_protocol):
        """Test connection_made sends raw telegram."""
        service.raw_input = "<S2113010000F02D12>"
        service.connection_made()
        mock_conbus_protocol.send_raw_telegram.assert_called_once_with(
            "<S2113010000F02D12>"
        )
