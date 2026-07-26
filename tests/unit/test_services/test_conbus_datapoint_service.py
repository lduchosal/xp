# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusDatapointService."""

from unittest.mock import Mock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

SERIAL_NUMBER = "0020012521"
OTHER_SERIAL_NUMBER = "0020012599"
TEMPERATURE_VALUE = "+26,0§C"
INITIAL_TIMEOUT_SECONDS = 0.25
TIMEOUT_SECONDS = 5.0
DEFAULT_QUERY_TIMEOUT_SECONDS = 1.0


def make_telegram_event(
    protocol: Mock,
    frame: str,
    serial_number: str,
    *,
    telegram_type: str = "R",
    checksum_valid: bool = True,
) -> TelegramReceivedEvent:
    """Build a TelegramReceivedEvent for tests.

    Args:
        protocol: Mocked ConbusEventProtocol carried by the event.
        frame: Full frame including angle brackets.
        serial_number: Serial number carried by the event.
        telegram_type: Telegram type letter (R, S, E).
        checksum_valid: Whether the frame checksum is valid.

    Returns:
        A TelegramReceivedEvent built without validation.

    """
    telegram = frame.strip("<>")
    return TelegramReceivedEvent.model_construct(
        protocol=protocol,
        frame=frame,
        telegram=telegram,
        payload=telegram[:-2],
        telegram_type=telegram_type,
        serial_number=serial_number,
        checksum=telegram[-2:],
        checksum_valid=checksum_valid,
    )


class TestConbusDatapointService:
    """Unit tests for ConbusDatapointService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self) -> Mock:
        """Create a mock ConbusEventProtocol with mocked signals.

        Returns:
            A mock ConbusEventProtocol with mocked signals.

        """
        protocol = Mock(spec=ConbusEventProtocol)
        protocol.on_connection_made = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_timeout = Mock()
        protocol.on_failed = Mock()
        protocol.timeout_seconds = INITIAL_TIMEOUT_SECONDS
        return protocol

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
    ) -> ConbusDatapointService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusDatapointService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    def make_temperature_reply(self, frame: str) -> ReplyTelegram:
        """Build a temperature datapoint reply telegram.

        Args:
            frame: Raw frame the reply was parsed from.

        Returns:
            A ReplyTelegram carrying a temperature datapoint.

        """
        return ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value=TEMPERATURE_VALUE,
            raw_telegram=frame,
            checksum="IL",
        )

    def test_service_initialization(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service initial state and signal wiring."""
        assert not service.serial_number
        assert service.datapoint_type is None
        assert service.service_response.success is False
        # Handlers are wired to the service's bound methods
        connect = mock_conbus_protocol.on_connection_made.connect
        assert connect.call_args[0][0] == service.connection_made
        connect = mock_conbus_protocol.on_telegram_received.connect
        assert connect.call_args[0][0] == service.telegram_received
        connect = mock_conbus_protocol.on_timeout.connect
        assert connect.call_args[0][0] == service.timeout
        connect = mock_conbus_protocol.on_failed.connect
        assert connect.call_args[0][0] == service.failed

    def test_query_datapoint_sets_parameters_and_timeout(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test query_datapoint stores parameters and applies timeout."""
        service.query_datapoint(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.TEMPERATURE,
            timeout_seconds=TIMEOUT_SECONDS,
        )

        assert service.serial_number == SERIAL_NUMBER
        assert service.datapoint_type == DataPointType.TEMPERATURE
        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_query_datapoint_default_timeout(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test query_datapoint applies its default one second timeout."""
        service.query_datapoint(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.TEMPERATURE,
        )

        assert mock_conbus_protocol.timeout_seconds == DEFAULT_QUERY_TIMEOUT_SECONDS

    def test_connection_made_sends_read_datapoint_telegram(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends F02D telegram for the datapoint."""
        service.query_datapoint(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.TEMPERATURE,
        )

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(DataPointType.TEMPERATURE.value),
        )

    def test_connection_made_without_datapoint_type_fails(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made fails when no datapoint type is set."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_not_called()
        finish_mock.assert_called_once_with(service.service_response)
        assert service.service_response.success is False
        assert service.service_response.error == "Datapoint type not set"

    def test_telegram_sent(self, service: ConbusDatapointService) -> None:
        """Test telegram_sent stores the sent telegram."""
        telegram = f"<S{SERIAL_NUMBER}F02D18FN>"

        service.telegram_sent(telegram)

        assert service.service_response.sent_telegram == telegram

    def test_telegram_received_matching_datapoint_succeeds(
        self,
        service: ConbusDatapointService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a matching datapoint reply completes the query with success."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.query_datapoint(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.TEMPERATURE,
        )
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"
        reply = self.make_temperature_reply(frame)
        mock_telegram_service.parse_reply_telegram.return_value = reply

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_called_once_with(service.service_response)
        response = service.service_response
        assert response.success is True
        assert response.serial_number == SERIAL_NUMBER
        assert response.system_function == SystemFunction.READ_DATAPOINT
        assert response.datapoint_type == DataPointType.TEMPERATURE
        assert response.datapoint_telegram == reply
        assert response.data_value == TEMPERATURE_VALUE
        assert response.received_telegrams == [frame]
        assert response.timestamp is not None
        assert response.timestamp.tzinfo is not None
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_telegram_received_ignores_other_serial_number(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test telegrams from other modules are recorded but not processed."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{OTHER_SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, OTHER_SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()
        assert service.service_response.received_telegrams == [frame]
        assert service.service_response.success is False

    def test_telegram_received_ignores_invalid_checksum(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test telegrams with invalid checksum are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"

        service.telegram_received(
            make_telegram_event(
                mock_conbus_protocol, frame, SERIAL_NUMBER, checksum_valid=False
            )
        )

        finish_mock.assert_not_called()
        assert service.service_response.success is False

    def test_telegram_received_ignores_non_reply_telegram(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test non-reply telegrams are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<S{SERIAL_NUMBER}F02D18FN>"

        service.telegram_received(
            make_telegram_event(
                mock_conbus_protocol, frame, SERIAL_NUMBER, telegram_type="S"
            )
        )

        finish_mock.assert_not_called()

    def test_telegram_received_ignores_unparseable_reply(
        self,
        service: ConbusDatapointService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies that cannot be parsed are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        mock_telegram_service.parse_reply_telegram.return_value = None
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()

    def test_telegram_received_ignores_other_datapoint_type(
        self,
        service: ConbusDatapointService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies for a different datapoint type are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        service.datapoint_type = DataPointType.MODULE_TYPE
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"
        mock_telegram_service.parse_reply_telegram.return_value = (
            self.make_temperature_reply(frame)
        )

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()
        assert service.service_response.success is False

    def test_telegram_received_ignores_other_system_function(
        self,
        service: ConbusDatapointService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies with a non READ_DATAPOINT function are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        service.datapoint_type = DataPointType.TEMPERATURE
        frame = f"<R{SERIAL_NUMBER}F18DFA>"
        mock_telegram_service.parse_reply_telegram.return_value = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.ACK,
            datapoint_type=DataPointType.TEMPERATURE,
            raw_telegram=frame,
            checksum="FA",
        )

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()

    def test_timeout_fails_with_timeout_error(
        self, service: ConbusDatapointService
    ) -> None:
        """Test timeout fails the query with a Timeout error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER

        service.timeout()

        finish_mock.assert_called_once_with(service.service_response)
        assert service.service_response.success is False
        assert service.service_response.error == "Timeout"
        assert service.service_response.serial_number == SERIAL_NUMBER

    def test_failed_emits_finish_with_error(
        self, service: ConbusDatapointService
    ) -> None:
        """Test failed emits on_finish with the error message."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection refused")

        finish_mock.assert_called_once_with(service.service_response)
        assert service.service_response.success is False
        assert service.service_response.error == "Connection refused"
        assert service.service_response.timestamp is not None
        assert service.service_response.timestamp.tzinfo is not None

    def test_set_timeout(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to protocol."""
        service.set_timeout(TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_start_reactor(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_context_manager_disconnects_signals(
        self, service: ConbusDatapointService, mock_conbus_protocol: Mock
    ) -> None:
        """Test context manager disconnects protocol signals on exit."""
        with service as s:
            assert s is service

        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()
