"""Unit tests for ConbusRawService."""

from unittest.mock import Mock

import pytest

from xp.models.conbus.conbus_client_config import ClientConfig, ConbusClientConfig
from xp.services.conbus.conbus_raw_service import ConbusRawService


class TestConbusRawService:
    """Unit tests for ConbusRawService functionality."""

    @pytest.fixture
    def mock_cli_config(self):
        """Create a test config."""
        client_config = ClientConfig(ip="10.0.0.1", port=8080, timeout=15)
        return ConbusClientConfig(conbus=client_config)

    @pytest.fixture
    def mock_reactor(self):
        """Create a mock reactor."""
        return Mock()

    @pytest.fixture
    def service(self, mock_cli_config, mock_reactor):
        """Create service instance with test config."""
        return ConbusRawService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
        )

    def test_service_initialization(self, service):
        """Test service can be initialized with required dependencies."""
        assert service.raw_input == ""
        assert service.progress_callback is None
        assert service.finish_callback is None
        assert service.service_response.success is False

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

    def test_telegram_received(self, service):
        """Test telegram_received callback updates service response."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        telegram_event = TelegramReceivedEvent(
            protocol=service,
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

    def test_telegram_received_multiple(self, service):
        """Test multiple telegram_received callbacks."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        telegram1 = TelegramReceivedEvent(
            protocol=service,
            frame="<R2113010000F02D12>",
            telegram="R2113010000F02D12",
            payload="R2113010000F02D",
            telegram_type="R",
            serial_number="2113010000",
            checksum="12",
            checksum_valid=True,
        )
        telegram2 = TelegramReceivedEvent(
            protocol=service,
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

    def test_telegram_received_with_progress_callback(self, service):
        """Test telegram_received calls progress callback."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        progress_mock = Mock()
        service.progress_callback = progress_mock

        telegram_event = TelegramReceivedEvent(
            protocol=service,
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
        """Test timeout callback."""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        result = service.timeout()

        assert result is False
        finish_mock.assert_called_once_with(service.service_response)

    def test_failed(self, service):
        """Test failed callback updates service response."""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        service.failed("Connection failed")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection failed"
        finish_mock.assert_called_once_with(service.service_response)
