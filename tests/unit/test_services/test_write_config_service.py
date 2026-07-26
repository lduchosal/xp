# Copyright (c) 2025 ldvchosal
"""Unit tests for WriteConfigService."""

from unittest.mock import Mock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.write_config_service import WriteConfigService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

SERIAL_NUMBER = "0012345008"
OTHER_SERIAL_NUMBER = "0012345999"
SHORT_SERIAL_NUMBER = "12345"
DATA_VALUE = "25"
INITIAL_TIMEOUT_SECONDS = 0.25
TIMEOUT_SECONDS = 5.0


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


class TestWriteConfigService:
    """Unit tests for WriteConfigService functionality."""

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
    ) -> WriteConfigService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return WriteConfigService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    def test_service_initialization(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service initial state and signal wiring."""
        assert not service.serial_number
        assert not service.data_value
        assert service.datapoint_type is None
        assert service.write_config_response.success is False
        # Handlers are wired to the service's bound methods
        connect = mock_conbus_protocol.on_connection_made.connect
        assert connect.call_args[0][0] == service.connection_made
        connect = mock_conbus_protocol.on_telegram_sent.connect
        assert connect.call_args[0][0] == service.telegram_sent
        connect = mock_conbus_protocol.on_telegram_received.connect
        assert connect.call_args[0][0] == service.telegram_received
        connect = mock_conbus_protocol.on_timeout.connect
        assert connect.call_args[0][0] == service.timeout
        connect = mock_conbus_protocol.on_failed.connect
        assert connect.call_args[0][0] == service.failed

    def test_write_config_sets_parameters_and_timeout(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test write_config stores parameters and applies timeout."""
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
            timeout_seconds=TIMEOUT_SECONDS,
        )

        assert service.serial_number == SERIAL_NUMBER
        assert service.datapoint_type == DataPointType.LINK_NUMBER
        assert service.data_value == DATA_VALUE
        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_write_config_without_timeout_keeps_protocol_timeout(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test write_config without timeout does not touch protocol timeout."""
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
        )

        assert mock_conbus_protocol.timeout_seconds == INITIAL_TIMEOUT_SECONDS

    def test_connection_made_sends_write_config_telegram(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends F04D telegram with datapoint and value."""
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
        )

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.WRITE_CONFIG,
            data_value=f"{DataPointType.LINK_NUMBER.value}{DATA_VALUE}",
        )

    def test_connection_made_rejects_invalid_serial_number(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made fails when serial number is not 10 digits."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.write_config(
            serial_number=SHORT_SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
        )

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_not_called()
        finish_mock.assert_called_once_with(service.write_config_response)
        assert service.write_config_response.success is False
        assert service.write_config_response.error is not None
        assert "Serial number must be 10 digits" in service.write_config_response.error

    def test_connection_made_rejects_short_data_value(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made fails when data value is shorter than 2 bytes."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value="1",
        )

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_not_called()
        finish_mock.assert_called_once_with(service.write_config_response)
        assert service.write_config_response.success is False
        assert service.write_config_response.error is not None
        assert "data_value must be at least 2 bytes" in (
            service.write_config_response.error
        )

    def test_connection_made_rejects_missing_datapoint_type(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made fails when datapoint type is not set."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        service.data_value = DATA_VALUE

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_not_called()
        finish_mock.assert_called_once_with(service.write_config_response)
        assert service.write_config_response.success is False
        assert service.write_config_response.error is not None
        assert "datapoint_type must be defined" in service.write_config_response.error

    def test_telegram_sent(self, service: WriteConfigService) -> None:
        """Test telegram_sent stores the sent telegram."""
        telegram = f"<S{SERIAL_NUMBER}F04D0425FN>"

        service.telegram_sent(telegram)

        assert service.write_config_response.sent_telegram == telegram

    def test_telegram_received_ack_finishes_with_success(
        self,
        service: WriteConfigService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test an ACK reply completes the operation successfully."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
        )
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

        finish_mock.assert_called_once_with(service.write_config_response)
        response = service.write_config_response
        assert response.success is True
        assert response.system_function == SystemFunction.ACK
        assert response.serial_number == SERIAL_NUMBER
        assert response.datapoint_type == DataPointType.LINK_NUMBER
        assert response.data_value == DATA_VALUE
        assert response.error is None
        assert response.received_telegrams == [frame]
        assert response.timestamp is not None
        assert response.timestamp.tzinfo is not None

    def test_telegram_received_nak_finishes_with_failure(
        self,
        service: WriteConfigService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test a NAK reply completes the operation as failed."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
        )
        frame = f"<R{SERIAL_NUMBER}F19DFB>"
        mock_telegram_service.parse_reply_telegram.return_value = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.NAK,
            raw_telegram=frame,
            checksum="FB",
        )

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_called_once_with(service.write_config_response)
        assert service.write_config_response.success is False
        assert service.write_config_response.system_function == SystemFunction.NAK

    def test_telegram_received_ignores_other_serial_number(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test telegrams from other modules are recorded but not processed."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{OTHER_SERIAL_NUMBER}F18DFA>"

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, OTHER_SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()
        assert service.write_config_response.received_telegrams == [frame]
        assert service.write_config_response.success is False

    def test_telegram_received_ignores_invalid_checksum(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test telegrams with invalid checksum are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{SERIAL_NUMBER}F18DFA>"

        service.telegram_received(
            make_telegram_event(
                mock_conbus_protocol, frame, SERIAL_NUMBER, checksum_valid=False
            )
        )

        finish_mock.assert_not_called()
        assert service.write_config_response.success is False

    def test_telegram_received_ignores_non_reply_telegram(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test non-reply telegrams are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<S{SERIAL_NUMBER}F04D0425FN>"

        service.telegram_received(
            make_telegram_event(
                mock_conbus_protocol, frame, SERIAL_NUMBER, telegram_type="S"
            )
        )

        finish_mock.assert_not_called()

    def test_telegram_received_ignores_unparseable_reply(
        self,
        service: WriteConfigService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies that cannot be parsed are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        mock_telegram_service.parse_reply_telegram.return_value = None
        frame = f"<R{SERIAL_NUMBER}F18DFA>"

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()

    def test_telegram_received_ignores_non_ack_nak_reply(
        self,
        service: WriteConfigService,
        mock_telegram_service: Mock,
        mock_conbus_protocol: Mock,
    ) -> None:
        """Test replies that are neither ACK nor NAK are ignored."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.serial_number = SERIAL_NUMBER
        frame = f"<R{SERIAL_NUMBER}F02D0425FN>"
        mock_telegram_service.parse_reply_telegram.return_value = ReplyTelegram(
            serial_number=SERIAL_NUMBER,
            system_function=SystemFunction.READ_DATAPOINT,
            raw_telegram=frame,
            checksum="FN",
        )

        service.telegram_received(
            make_telegram_event(mock_conbus_protocol, frame, SERIAL_NUMBER)
        )

        finish_mock.assert_not_called()

    def test_timeout_finishes_with_error(self, service: WriteConfigService) -> None:
        """Test timeout finishes the operation with a Timeout error."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        finish_mock.assert_called_once_with(service.write_config_response)
        assert service.write_config_response.success is False
        assert service.write_config_response.error == "Timeout"

    def test_failed_finishes_with_error_message(
        self, service: WriteConfigService
    ) -> None:
        """Test failed finishes the operation with the given message."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection refused")

        finish_mock.assert_called_once_with(service.write_config_response)
        assert service.write_config_response.success is False
        assert service.write_config_response.error == "Connection refused"

    def test_set_timeout(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to protocol."""
        service.set_timeout(TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == TIMEOUT_SECONDS

    def test_start_reactor(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_context_manager_resets_state_and_disconnects(
        self, service: WriteConfigService, mock_conbus_protocol: Mock
    ) -> None:
        """Test context manager resets state and disconnects on exit."""
        service.write_config(
            serial_number=SERIAL_NUMBER,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=DATA_VALUE,
        )

        with service as s:
            assert s is service
            assert not s.serial_number
            assert not s.data_value
            assert s.datapoint_type is None
            assert s.write_config_response.success is False

        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()
