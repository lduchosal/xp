"""Unit tests for ConbusLightlevelService."""

from unittest.mock import Mock, patch

import pytest

from xp.models.conbus.conbus_client_config import ClientConfig, ConbusClientConfig
from xp.services.conbus.conbus_lightlevel_set_service import ConbusLightlevelSetService


class TestConbusLightlevelService:
    """Unit tests for ConbusLightlevelService functionality."""

    @pytest.fixture
    def mock_cli_config(self):
        """Create a test config"""
        client_config = ClientConfig(ip="10.0.0.1", port=8080, timeout=15)
        return ConbusClientConfig(conbus=client_config)

    @pytest.fixture
    def mock_reactor(self):
        """Create a mock reactor"""
        return Mock()

    @pytest.fixture
    def service(self, mock_cli_config, mock_reactor):
        """Create service instance with test config"""
        return ConbusLightlevelSetService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
        )

    def test_service_initialization(self, service):
        """Test service can be initialized with required dependencies"""
        assert service.serial_number == ""
        assert service.output_number == 0
        assert service.level == 0
        assert service.finish_callback is None
        assert service.service_response.success is False

    def test_service_context_manager(self, service):
        """Test service can be used as context manager"""
        with service as s:
            assert s is service

    def test_connection_established(self, service):
        """Test connection_established sends telegram"""
        service.serial_number = "0012345008"
        service.output_number = 2
        service.level = 50

        # Mock send_telegram to avoid transport issues in unit tests
        with patch.object(service, "send_telegram"):
            service.connection_established()

    def test_telegram_sent(self, service):
        """Test telegram_sent callback updates service response"""
        telegram = "<S0012345008F0415020:050FN>"
        service.telegram_sent(telegram)

        assert service.service_response.sent_telegram == telegram

    def test_telegram_received(self, service):
        """Test telegram_received callback with valid response"""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        service.serial_number = "0012345008"
        service.output_number = 2
        service.level = 50

        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0012345008F18DFA>",
            telegram="R0012345008F18DFA",
            payload="R0012345008F18D",
            telegram_type="R",
            serial_number="0012345008",
            checksum="FA",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        assert service.service_response.success is True
        assert service.service_response.received_telegrams == ["<R0012345008F18DFA>"]
        assert service.service_response.level == 50

    def test_telegram_received_wrong_serial(self, service):
        """Test telegram_received ignores telegrams from different serial"""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        service.serial_number = "0012345008"

        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0012345999F18DFA>",
            telegram="R0012345999F18DFA",
            payload="R0012345999F18D",
            telegram_type="R",
            serial_number="0012345999",
            checksum="FA",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        # Should still record the telegram but not process it
        assert service.service_response.received_telegrams == ["<R0012345999F18DFA>"]
        assert service.service_response.success is False

    def test_telegram_received_with_callback(self, service):
        """Test telegram_received calls finish callback"""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        finish_mock = Mock()
        service.finish_callback = finish_mock
        service.serial_number = "0012345008"
        service.output_number = 2
        service.level = 50

        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0012345008F18DFA>",
            telegram="R0012345008F18DFA",
            payload="R0012345008F18D",
            telegram_type="R",
            serial_number="0012345008",
            checksum="FA",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        finish_mock.assert_called_once_with(service.service_response)

    def test_failed(self, service):
        """Test failed callback updates service response"""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        service.failed("Connection timeout")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.service_response)

    def test_set_lightlevel_invalid_output(self, service):
        """Test set_lightlevel with invalid output number"""
        finish_mock = Mock()

        service.set_lightlevel("0012345008", 10, 50, finish_mock)

        # Should call callback with error
        assert finish_mock.called
        response = finish_mock.call_args[0][0]
        assert response.success is False
        assert "Output number must be between 0 and 8" in response.error

    def test_set_lightlevel_invalid_level(self, service):
        """Test set_lightlevel with invalid level"""
        finish_mock = Mock()

        service.set_lightlevel("0012345008", 2, 150, finish_mock)

        # Should call callback with error
        assert finish_mock.called
        response = finish_mock.call_args[0][0]
        assert response.success is False
        assert "Light level must be between 0 and 100" in response.error

    def test_turn_off(self, service):
        """Test turn_off delegates to set_lightlevel with level 0"""
        finish_mock = Mock()

        with patch.object(service, "set_lightlevel") as mock_set:
            service.turn_off("0012345008", 2, finish_mock)

        mock_set.assert_called_once_with("0012345008", 2, 0, finish_mock, None)

    def test_turn_on(self, service):
        """Test turn_on delegates to set_lightlevel with level 80"""
        finish_mock = Mock()

        with patch.object(service, "set_lightlevel") as mock_set:
            service.turn_on("0012345008", 2, finish_mock)

        mock_set.assert_called_once_with("0012345008", 2, 80, finish_mock, None)
