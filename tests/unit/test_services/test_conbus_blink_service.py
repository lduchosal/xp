"""Unit tests for ConbusBlinkService."""

from unittest.mock import Mock

import pytest

from xp.models.telegram.system_function import SystemFunction
from xp.services.conbus.conbus_blink_service import ConbusBlinkService


class TestConbusBlinkService:
    """Unit tests for ConbusBlinkService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create a mock ConbusEventProtocol."""
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
        mock_protocol.send_telegram = Mock()
        mock_protocol.start_reactor = Mock()
        mock_protocol.stop_reactor = Mock()
        return mock_protocol

    @pytest.fixture
    def mock_telegram_service(self):
        """Create a mock telegram service."""
        return Mock()

    @pytest.fixture
    def service(self, mock_conbus_protocol, mock_telegram_service):
        """Create service instance with test dependencies."""
        return ConbusBlinkService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    def test_service_initialization(self, service, mock_conbus_protocol):
        """Test service can be initialized with required dependencies."""
        assert service.serial_number == ""
        assert service.on_or_off == "none"
        assert service.service_response.success is False
        assert service.service_response.system_function == SystemFunction.NONE
        assert service.service_response.operation == "none"
        # Verify signal connections
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_service_context_manager(self, service, mock_conbus_protocol):
        """Test service can be used as context manager."""
        with service as s:
            assert s is service
            # State should be reset
            assert s.serial_number == ""
            assert s.on_or_off == "none"
        # Signals should be disconnected after exit
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_connection_made_blink_on(self, service, mock_conbus_protocol):
        """Test connection_made configures for 'on' operation."""
        service.serial_number = "0012345008"
        service.on_or_off = "on"

        service.connection_made()

        assert service.service_response.system_function == SystemFunction.BLINK
        assert service.service_response.operation == "on"
        mock_conbus_protocol.send_telegram.assert_called_once()

    def test_connection_made_blink_off(self, service, mock_conbus_protocol):
        """Test connection_made configures for 'off' operation."""
        service.serial_number = "0012345008"
        service.on_or_off = "off"

        service.connection_made()

        assert service.service_response.system_function == SystemFunction.UNBLINK
        assert service.service_response.operation == "off"
        mock_conbus_protocol.send_telegram.assert_called_once()

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

    def test_telegram_received_ack(
        self, service, mock_telegram_service, mock_conbus_protocol
    ):
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

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
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

    def test_telegram_received_nak(
        self, service, mock_telegram_service, mock_conbus_protocol
    ):
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

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
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

    def test_telegram_received_wrong_serial(self, service, mock_conbus_protocol):
        """Test telegram_received ignores telegrams from different serial."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent

        service.serial_number = "0012345008"

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
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

    def test_telegram_received_emits_signal(
        self, service, mock_telegram_service, mock_conbus_protocol
    ):
        """Test telegram_received emits on_finish signal."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.reply_telegram import ReplyTelegram

        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = "0012345008"

        # Mock reply telegram
        mock_reply = ReplyTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.ACK,
            raw_telegram="<R0012345008F18DFA>",
            checksum="FA",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
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
        """Test failed emits on_finish signal with error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection timeout")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection timeout"
        finish_mock.assert_called_once_with(service.service_response)

    def test_timeout(self, service):
        """Test timeout emits on_finish signal with error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        assert service.service_response.success is False
        assert service.service_response.error == "Blink operation timeout"
        finish_mock.assert_called_once_with(service.service_response)

    def test_set_timeout(self, service, mock_conbus_protocol):
        """Test set_timeout delegates to protocol."""
        service.set_timeout(5.0)

        assert mock_conbus_protocol.timeout_seconds == 5.0

    def test_start_reactor(self, service, mock_conbus_protocol):
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(self, service, mock_conbus_protocol):
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()
