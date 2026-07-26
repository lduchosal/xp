# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusCustomService."""

from unittest.mock import Mock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_custom_service import ConbusCustomService

# Serial number used by the fake target module in these tests.
SERIAL_NUMBER = "0012345008"

# Timeout values used to exercise timeout delegation.
TIMEOUT_SECONDS = 1.5
UPDATED_TIMEOUT_SECONDS = 5.0


class TestConbusCustomService:
    """Unit tests for ConbusCustomService functionality."""

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
    ) -> ConbusCustomService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusCustomService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    @staticmethod
    def make_reply_event(
        mock_conbus_protocol: Mock,
        payload: str,
        *,
        checksum_valid: bool = True,
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
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service can be initialized with required dependencies."""
        assert not service.serial_number
        assert not service.function_code
        assert not service.data
        assert service.service_response.success is False
        # Verify signal connections
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_connection_made_sends_custom_telegram(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends the configured custom telegram."""
        service.serial_number = SERIAL_NUMBER
        service.function_code = "02"
        service.data = "E2"

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            serial_number=SERIAL_NUMBER,
            telegram_type=TelegramType.SYSTEM,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value="E2",
        )

    def test_connection_made_invalid_function_code(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made fails on an unknown function code."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        service.function_code = "ZZ"
        service.data = "00"

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_not_called()
        assert service.service_response.success is False
        assert service.service_response.error == "Invalid function code ZZ"
        finish_mock.assert_called_once_with(service.service_response)

    def test_telegram_sent(self, service: ConbusCustomService) -> None:
        """Test telegram_sent records the sent telegram in the response."""
        telegram = f"<S{SERIAL_NUMBER}F02DE2FM>"

        service.telegram_sent(telegram)

        assert service.service_response.sent_telegram == telegram

    def test_telegram_received_reply(
        self,
        service: ConbusCustomService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a matching reply completes the response and emits on_finish."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        service.function_code = "02"
        service.data = "E2"
        mock_reply = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            raw_telegram=f"<R{SERIAL_NUMBER}F02DE2FM>",
            checksum="FM",
        )
        mock_telegram_service.parse_telegram.return_value = mock_reply
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F02DE2")

        service.telegram_received(event)

        assert service.service_response.success is True
        assert service.service_response.serial_number == SERIAL_NUMBER
        assert service.service_response.function_code == "02"
        assert service.service_response.data == "E2"
        assert service.service_response.reply_telegram == mock_reply
        assert service.service_response.received_telegrams == [event.frame]
        assert service.service_response.timestamp is not None
        mock_telegram_service.parse_telegram.assert_called_once_with(event.frame)
        finish_mock.assert_called_once_with(service.service_response)

    def test_telegram_received_non_reply_parse_result(
        self,
        service: ConbusCustomService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a parse result that is not a ReplyTelegram is not stored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        mock_telegram_service.parse_telegram.return_value = SystemTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            raw_telegram=f"<S{SERIAL_NUMBER}F02DE2FM>",
            checksum="FM",
        )
        event = self.make_reply_event(mock_conbus_protocol, f"R{SERIAL_NUMBER}F02DE2")

        service.telegram_received(event)

        assert service.service_response.success is True
        assert service.service_response.reply_telegram is None
        finish_mock.assert_called_once_with(service.service_response)

    def test_telegram_received_invalid_checksum_ignored(
        self,
        service: ConbusCustomService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a reply with invalid checksum is recorded but not processed."""
        service.serial_number = SERIAL_NUMBER
        event = self.make_reply_event(
            mock_conbus_protocol, f"R{SERIAL_NUMBER}F02DE2", checksum_valid=False
        )

        service.telegram_received(event)

        assert service.service_response.received_telegrams == [event.frame]
        assert service.service_response.success is False
        mock_telegram_service.parse_telegram.assert_not_called()

    def test_telegram_received_wrong_serial_ignored(
        self,
        service: ConbusCustomService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a reply from another module is recorded but not processed."""
        service.serial_number = SERIAL_NUMBER
        event = self.make_reply_event(mock_conbus_protocol, "R0099999999F02DE2")

        service.telegram_received(event)

        assert service.service_response.received_telegrams == [event.frame]
        assert service.service_response.success is False
        mock_telegram_service.parse_telegram.assert_not_called()

    def test_telegram_received_non_reply_ignored(
        self,
        service: ConbusCustomService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a non-reply telegram is recorded but not processed."""
        service.serial_number = SERIAL_NUMBER
        event = self.make_reply_event(mock_conbus_protocol, f"E{SERIAL_NUMBER}F02DE2")

        service.telegram_received(event)

        assert service.service_response.received_telegrams == [event.frame]
        assert service.service_response.success is False
        mock_telegram_service.parse_telegram.assert_not_called()

    def test_timeout(self, service: ConbusCustomService) -> None:
        """Test timeout emits on_finish with a Timeout error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        assert service.service_response.success is False
        assert service.service_response.error == "Timeout"
        finish_mock.assert_called_once_with(service.service_response)

    def test_failed(self, service: ConbusCustomService) -> None:
        """Test failed emits on_finish with the failure message."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection refused")

        assert service.service_response.success is False
        assert service.service_response.error == "Connection refused"
        assert service.service_response.timestamp is not None
        finish_mock.assert_called_once_with(service.service_response)

    def test_send_custom_telegram_with_timeout(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test send_custom_telegram stores parameters and timeout."""
        service.send_custom_telegram(
            serial_number=SERIAL_NUMBER,
            function_code="02",
            data="E2",
            timeout_seconds=TIMEOUT_SECONDS,
        )

        assert service.serial_number == SERIAL_NUMBER
        assert service.function_code == "02"
        assert service.data == "E2"
        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_send_custom_telegram_without_timeout(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test send_custom_telegram keeps the protocol timeout unchanged."""
        initial_timeout = mock_conbus_protocol.timeout_seconds

        service.send_custom_telegram(
            serial_number=SERIAL_NUMBER,
            function_code="17",
            data="AA",
        )

        assert service.serial_number == SERIAL_NUMBER
        assert service.function_code == "17"
        assert service.data == "AA"
        assert mock_conbus_protocol.timeout_seconds == initial_timeout

    def test_set_timeout(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to protocol."""
        service.set_timeout(UPDATED_TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == UPDATED_TIMEOUT_SECONDS

    def test_start_reactor(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_service_context_manager(
        self, service: ConbusCustomService, mock_conbus_protocol: Mock
    ) -> None:
        """Test context manager resets state and disconnects signals."""
        service.serial_number = SERIAL_NUMBER
        service.function_code = "02"
        service.data = "E2"

        with service as s:
            assert s is service
            # State should be reset
            assert not s.serial_number
            assert not s.function_code
            assert not s.data
            assert s.service_response.success is False
        # Signals should be disconnected after exit
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()
