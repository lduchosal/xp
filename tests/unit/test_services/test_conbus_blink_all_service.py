# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusBlinkAllService."""

from unittest.mock import Mock, call

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_blink_all_service import ConbusBlinkAllService

# Serial number used by the fake discovered module in these tests.
SERIAL_NUMBER = "0012345008"

# Timeout values used to exercise timeout delegation.
TIMEOUT_SECONDS = 1.5
UPDATED_TIMEOUT_SECONDS = 5.0


class TestConbusBlinkAllService:
    """Unit tests for ConbusBlinkAllService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self) -> Mock:
        """Create a mock ConbusEventProtocol.

        Returns:
            A mock ConbusEventProtocol.

        """
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
        mock_protocol.timeout_seconds = 0.25
        return mock_protocol

    @pytest.fixture
    def mock_telegram_service(self) -> Mock:
        """Create a mock telegram service.

        Returns:
            A mock telegram service.

        """
        return Mock()

    @pytest.fixture
    def service(
        self, mock_conbus_protocol: Mock, mock_telegram_service: Mock
    ) -> ConbusBlinkAllService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusBlinkAllService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    @staticmethod
    def make_reply_event(
        mock_conbus_protocol: Mock, payload: str, *, checksum_valid: bool = True
    ) -> TelegramReceivedEvent:
        """Build a TelegramReceivedEvent for a reply payload.

        Args:
            mock_conbus_protocol: Mock protocol carried by the event.
            payload: Telegram payload (frame without checksum and brackets).
            checksum_valid: Whether the event checksum is valid.

        Returns:
            TelegramReceivedEvent for the payload.

        """
        return TelegramReceivedEvent.model_construct(
            protocol=mock_conbus_protocol,
            frame=f"<{payload}FM>",
            telegram=f"{payload}FM",
            payload=payload,
            telegram_type=payload[0],
            serial_number=payload[1:11],
            checksum="FM",
            checksum_valid=checksum_valid,
        )

    def test_service_initialization(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service can be initialized with required dependencies."""
        assert not service.serial_number
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

    def test_connection_made_sends_broadcast_discover(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends a broadcast discovery telegram."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )
        progress_mock.assert_called_once_with(".")

    def test_send_blink_on(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test send_blink sends BLINK telegram for the 'on' operation."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.on_or_off = "on"

        service.send_blink(SERIAL_NUMBER)

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.BLINK,
            data_value="00",
        )
        assert service.service_response.system_function == SystemFunction.BLINK
        assert service.service_response.operation == "on"
        progress_mock.assert_called_once_with(".")

    def test_send_blink_off(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test send_blink sends UNBLINK telegram for the 'off' operation."""
        service.on_or_off = "off"

        service.send_blink(SERIAL_NUMBER)

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.UNBLINK,
            data_value="00",
        )
        assert service.service_response.system_function == SystemFunction.UNBLINK
        assert service.service_response.operation == "off"

    def test_telegram_sent(
        self, service: ConbusBlinkAllService, mock_telegram_service: Mock
    ) -> None:
        """Test telegram_sent parses and records the sent telegram."""
        telegram = f"<S{SERIAL_NUMBER}F05D00FN>"
        mock_system_telegram = SystemTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.BLINK,
            raw_telegram=telegram,
            checksum="FN",
        )
        mock_telegram_service.parse_system_telegram.return_value = mock_system_telegram

        service.telegram_sent(telegram)

        assert service.service_response.sent_telegram == mock_system_telegram
        mock_telegram_service.parse_system_telegram.assert_called_once_with(telegram)

    def test_telegram_received_discovery_reply_triggers_blink(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a discovery reply triggers a blink telegram to that module."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.on_or_off = "on"
        mock_reply = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.DISCOVERY,
            raw_telegram=f"<R{SERIAL_NUMBER}F01DFM>",
            checksum="FM",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")

        service.telegram_received(event)

        assert service.service_response.received_telegrams == [event.frame]
        mock_telegram_service.parse_reply_telegram.assert_called_once_with(event.frame)
        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.BLINK,
            data_value="00",
        )
        # One progress event from send_blink, one from telegram_received
        assert progress_mock.call_args_list == [call("."), call(".")]

    def test_telegram_received_blink_reply(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a blink acknowledgment emits progress without sending more."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        mock_reply = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.BLINK,
            raw_telegram=f"<R{SERIAL_NUMBER}F05D00FM>",
            checksum="FM",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F05D00")

        service.telegram_received(event)

        progress_mock.assert_called_once_with(".")
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_unblink_reply(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test an unblink acknowledgment emits progress without sending more."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        mock_reply = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.UNBLINK,
            raw_telegram=f"<R{SERIAL_NUMBER}F06D00FM>",
            checksum="FM",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F06D00")

        service.telegram_received(event)

        progress_mock.assert_called_once_with(".")
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_invalid_checksum_ignored(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a reply with invalid checksum is recorded but not parsed."""
        event = self.make_reply_event(
            mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D", checksum_valid=False
        )

        service.telegram_received(event)

        assert service.service_response.received_telegrams == [event.frame]
        mock_telegram_service.parse_reply_telegram.assert_not_called()
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_non_reply_ignored(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a non-reply telegram is recorded but not parsed."""
        event = self.make_reply_event(mock_conbus_protocol, f"E{SERIAL_NUMBER}F01D")

        service.telegram_received(event)

        assert service.service_response.received_telegrams == [event.frame]
        mock_telegram_service.parse_reply_telegram.assert_not_called()
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_unexpected_reply(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test an unexpected reply neither blinks nor emits progress."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        mock_reply = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.ACK,
            raw_telegram=f"<R{SERIAL_NUMBER}F18DFM>",
            checksum="FM",
        )
        mock_telegram_service.parse_reply_telegram.return_value = mock_reply
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F18D")

        service.telegram_received(event)

        progress_mock.assert_not_called()
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_unparseable_reply(
        self,
        service: ConbusBlinkAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test an unparseable reply neither blinks nor emits progress."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        mock_telegram_service.parse_reply_telegram.return_value = None
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F01D")

        service.telegram_received(event)

        progress_mock.assert_not_called()
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_timeout(self, service: ConbusBlinkAllService) -> None:
        """Test timeout emits on_finish with an error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        assert service.service_response.success is False
        assert service.service_response.error == "Blink all operation timeout"
        finish_mock.assert_called_once_with(service.service_response)

    def test_failed(self, service: ConbusBlinkAllService) -> None:
        """Test failed emits on_finish with the failure message."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection refused")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection refused"
        assert service.service_response.timestamp is not None
        finish_mock.assert_called_once_with(service.service_response)

    def test_send_blink_all_telegram_with_timeout(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test send_blink_all_telegram stores operation and timeout."""
        service.send_blink_all_telegram("on", timeout_seconds=TIMEOUT_SECONDS)

        assert service.on_or_off == "on"
        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_send_blink_all_telegram_without_timeout(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test send_blink_all_telegram keeps the protocol timeout unchanged."""
        initial_timeout = mock_conbus_protocol.timeout_seconds

        service.send_blink_all_telegram("off")

        assert service.on_or_off == "off"
        assert mock_conbus_protocol.timeout_seconds == initial_timeout

    def test_set_timeout(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to protocol."""
        service.set_timeout(UPDATED_TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == UPDATED_TIMEOUT_SECONDS

    def test_start_reactor(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_service_context_manager(
        self, service: ConbusBlinkAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test context manager resets state and disconnects signals."""
        service.serial_number = SERIAL_NUMBER
        service.on_or_off = "on"

        with service as s:
            assert s is service
            # State should be reset
            assert not s.serial_number
            assert s.on_or_off == "none"
            assert s.service_response.success is False
            assert s.service_response.operation == "none"
        # Signals should be disconnected after exit
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()
