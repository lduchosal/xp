# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusDatapointQueryAllService."""

from unittest.mock import Mock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_datapoint_queryall_service import (
    ConbusDatapointQueryAllService,
)
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

SERIAL_NUMBER = "0020012521"
OTHER_SERIAL_NUMBER = "0020012599"
TEMPERATURE_VALUE = "+26,0§C"
INITIAL_TIMEOUT_SECONDS = 0.25
TIMEOUT_SECONDS = 5.0
INDEX_AFTER_FIRST_QUERY = 1
INDEX_AFTER_SECOND_QUERY = 2


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


class TestConbusDatapointQueryAllService:
    """Unit tests for ConbusDatapointQueryAllService functionality."""

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
    ) -> ConbusDatapointQueryAllService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusDatapointQueryAllService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    def test_service_initialization(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service initial state and signal wiring."""
        assert not service.serial_number
        assert service.current_index == 0
        assert service.datapoint_types == list(DataPointType)
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

    def test_query_all_datapoints_sets_parameters_and_timeout(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test query_all_datapoints stores serial number and applies timeout."""
        service.query_all_datapoints(
            serial_number=SERIAL_NUMBER,
            timeout_seconds=TIMEOUT_SECONDS,
        )

        assert service.serial_number == SERIAL_NUMBER
        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_query_all_datapoints_without_timeout_keeps_protocol_timeout(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test query_all_datapoints without timeout keeps protocol timeout."""
        service.query_all_datapoints(serial_number=SERIAL_NUMBER)

        assert mock_conbus_protocol.timeout_seconds == INITIAL_TIMEOUT_SECONDS

    def test_connection_made_queries_first_datapoint(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends the first datapoint query."""
        service.query_all_datapoints(serial_number=SERIAL_NUMBER)

        service.connection_made()

        first_datapoint = next(iter(DataPointType))
        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(first_datapoint.value),
        )
        assert service.current_index == INDEX_AFTER_FIRST_QUERY

    def test_next_datapoint_advances_through_types(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test next_datapoint sends queries in datapoint type order."""
        service.serial_number = SERIAL_NUMBER

        assert service.next_datapoint() is True
        assert service.next_datapoint() is True

        assert service.current_index == INDEX_AFTER_SECOND_QUERY
        sent_values = [
            call.kwargs["data_value"]
            for call in mock_conbus_protocol.send_telegram.call_args_list
        ]
        expected_types = list(DataPointType)[:INDEX_AFTER_SECOND_QUERY]
        assert sent_values == [str(dp.value) for dp in expected_types]

    def test_next_datapoint_queries_every_datapoint_type(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test next_datapoint covers all datapoint types then stops."""
        service.serial_number = SERIAL_NUMBER

        while service.next_datapoint():
            pass

        assert service.current_index == len(service.datapoint_types)
        assert mock_conbus_protocol.send_telegram.call_count == len(
            service.datapoint_types
        )
        sent_values = [
            call.kwargs["data_value"]
            for call in mock_conbus_protocol.send_telegram.call_args_list
        ]
        assert sent_values == [str(dp.value) for dp in DataPointType]

    def test_next_datapoint_exhausted_returns_false(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test next_datapoint returns False when all types were queried."""
        service.serial_number = SERIAL_NUMBER
        service.current_index = len(service.datapoint_types)

        assert service.next_datapoint() is False
        mock_conbus_protocol.send_telegram.assert_not_called()

    def test_timeout_queries_next_datapoint(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test timeout moves on to the next datapoint without finishing."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER

        service.timeout()

        mock_conbus_protocol.send_telegram.assert_called_once()
        finish_mock.assert_not_called()

    def test_timeout_after_last_datapoint_finishes(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test timeout after the last datapoint emits on_finish with success."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        service.current_index = len(service.datapoint_types)

        service.timeout()

        mock_conbus_protocol.send_telegram.assert_not_called()
        finish_mock.assert_called_once_with(service.service_response)
        response = service.service_response
        assert response.success is True
        assert response.serial_number == SERIAL_NUMBER
        assert response.system_function == SystemFunction.READ_DATAPOINT
        assert response.timestamp is not None
        assert response.timestamp.tzinfo is not None

    def test_telegram_sent(self, service: ConbusDatapointQueryAllService) -> None:
        """Test telegram_sent stores the sent telegram."""
        telegram = f"<S{SERIAL_NUMBER}F02D00FN>"

        service.telegram_sent(telegram)

        assert service.service_response.sent_telegram == telegram

    def test_telegram_received_emits_progress(
        self,
        service: ConbusDatapointQueryAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a datapoint reply emits on_progress with the parsed telegram."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"
        reply = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value=TEMPERATURE_VALUE,
            raw_telegram=frame,
            checksum="IL",
        )
        mock_telegram_service.parse_reply_telegram.return_value = reply

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        progress_mock.assert_called_once_with(reply)
        assert service.service_response.received_telegrams == [frame]

    def test_telegram_received_ignores_other_serial_number(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test telegrams from other modules are recorded but not processed."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{OTHER_SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, OTHER_SERIAL_NUMBER)
        )

        progress_mock.assert_not_called()
        assert service.service_response.received_telegrams == [frame]

    def test_telegram_received_ignores_invalid_checksum(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test telegrams with invalid checksum are ignored."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"

        service.telegram_received(
            make_telegram_event(
                mock_conbus_protocol, frame, SERIAL_NUMBER, checksum_valid=False
            )
        )

        progress_mock.assert_not_called()

    def test_telegram_received_ignores_non_reply_telegram(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test non-reply telegrams are ignored."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<S{SERIAL_NUMBER}F02D00FN>"

        service.telegram_received(
            make_telegram_event(
                mock_conbus_protocol, frame, SERIAL_NUMBER, telegram_type="S"
            )
        )

        progress_mock.assert_not_called()

    def test_telegram_received_ignores_unparseable_reply(
        self,
        service: ConbusDatapointQueryAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies that cannot be parsed are ignored."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.serial_number = SERIAL_NUMBER
        mock_telegram_service.parse_reply_telegram.return_value = None
        frame = f"<R{SERIAL_NUMBER}F02D18{TEMPERATURE_VALUE}IL>"

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        progress_mock.assert_not_called()

    def test_telegram_received_ignores_other_system_function(
        self,
        service: ConbusDatapointQueryAllService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies with a non READ_DATAPOINT function are ignored."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{SERIAL_NUMBER}F18DFA>"
        mock_telegram_service.parse_reply_telegram.return_value = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.ACK,
            raw_telegram=frame,
            checksum="FA",
        )

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        progress_mock.assert_not_called()

    def test_failed_emits_finish_with_error(
        self, service: ConbusDatapointQueryAllService
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
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to protocol."""
        service.set_timeout(TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_start_reactor(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_context_manager_resets_state_and_disconnects(
        self, service: ConbusDatapointQueryAllService, mock_conbus_protocol: Mock
    ) -> None:
        """Test context manager resets state and disconnects on exit."""
        service.serial_number = SERIAL_NUMBER
        service.current_index = INDEX_AFTER_SECOND_QUERY
        service.service_response.success = True

        with service as s:
            assert s is service
            assert not s.serial_number
            assert s.current_index == 0
            assert s.datapoint_types == list(DataPointType)
            assert s.service_response.success is False

        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()
