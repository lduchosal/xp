"""Unit tests for ConbusBlinkService."""

from unittest.mock import Mock

import pytest

from xp.models.conbus.conbus_client_config import ClientConfig, ConbusClientConfig
from xp.models.telegram.system_function import SystemFunction
from xp.services.conbus.conbus_blink_service import ConbusBlinkService


class TestConbusBlinkService:
    """Unit tests for ConbusBlinkService functionality."""

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
    def mock_telegram_service(self):
        """Create a mock telegram service."""
        return Mock()

    @pytest.fixture
    def service(self, mock_telegram_service, mock_cli_config, mock_reactor):
        """Create service instance with test config."""
        return ConbusBlinkService(
            telegram_service=mock_telegram_service,
            cli_config=mock_cli_config,
            reactor=mock_reactor,
        )

    def test_service_initialization(self, service):
        """Test service can be initialized with required dependencies."""
        assert service.serial_number == ""
        assert service.on_or_off == "none"
        assert service.finish_callback is None
        assert service.service_response.success is False
        assert service.service_response.system_function == SystemFunction.NONE
        assert service.service_response.operation == "none"

    def test_service_context_manager(self, service):
        """Test service can be used as context manager."""
        with service as s:
            assert s is service

    def test_connection_established_blink_on(self, service):
        """Test connection_established configures for 'on' operation."""
        from unittest.mock import patch

        service.serial_number = "0012345008"
        service.on_or_off = "on"

        # Mock send_telegram to avoid transport issues in unit tests
        with patch.object(service, "send_telegram"):
            service.connection_established()

        assert service.service_response.system_function == SystemFunction.BLINK
        assert service.service_response.operation == "on"

    def test_connection_established_blink_off(self, service):
        """Test connection_established configures for 'off' operation."""
        from unittest.mock import patch

        service.serial_number = "0012345008"
        service.on_or_off = "off"

        # Mock send_telegram to avoid transport issues in unit tests
        with patch.object(service, "send_telegram"):
            service.connection_established()

        assert service.service_response.system_function == SystemFunction.UNBLINK
        assert service.service_response.operation == "off"

    def test_telegram_sent(self, service, mock_telegram_service):
        """Test telegram_sent callback updates service response."""
        from xp.models.telegram.system_telegram import SystemTelegram

        telegram = "<S0012345008F05D00FN>"
        mock_system_telegram = SystemTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.BLINK,
            raw_telegram=telegram,
            checksum="FN",
        )
        mock_telegram_service.parse_system_telegram.return_value = mock_system_telegram

        service.telegram_sent(telegram)

        assert service.service_response.sent_telegram == mock_system_telegram
        mock_telegram_service.parse_system_telegram.assert_called_once_with(telegram)

    def test_telegram_received_ack(self, service, mock_telegram_service):
        """Test telegram_received callback with ACK response."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.reply_telegram import ReplyTelegram

        service.serial_number = "0012345008"

        # Mock reply telegram
        mock_reply = ReplyTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.ACK,
            raw_telegram="<R0012345008F18DFA>",
            checksum="FA",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply

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
        assert service.service_response.reply_telegram == mock_reply

    def test_telegram_received_nak(self, service, mock_telegram_service):
        """Test telegram_received callback with NAK response."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.reply_telegram import ReplyTelegram

        service.serial_number = "0012345008"

        # Mock reply telegram
        mock_reply = ReplyTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.NAK,
            raw_telegram="<R0012345008F19DFB>",
            checksum="FB",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply

        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0012345008F19DFB>",
            telegram="R0012345008F19DFB",
            payload="R0012345008F19D",
            telegram_type="R",
            serial_number="0012345008",
            checksum="FB",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        assert service.service_response.success is True
        assert service.service_response.received_telegrams == ["<R0012345008F19DFB>"]
        assert service.service_response.reply_telegram == mock_reply

    def test_telegram_received_wrong_serial(self, service, mock_telegram_service):
        """Test telegram_received ignores telegrams from different serial."""
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

    def test_telegram_received_with_callback(self, service, mock_telegram_service):
        """Test telegram_received calls finish callback."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.reply_telegram import ReplyTelegram

        finish_mock = Mock()
        service.finish_callback = finish_mock
        service.serial_number = "0012345008"

        # Mock reply telegram
        mock_reply = ReplyTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.ACK,
            raw_telegram="<R0012345008F18DFA>",
            checksum="FA",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply

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
        """Test failed callback updates service response."""
        finish_mock = Mock()
        service.finish_callback = finish_mock

        service.failed("Connection timeout")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.service_response)
