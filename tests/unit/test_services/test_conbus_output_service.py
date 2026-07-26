# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusOutputService."""

from unittest.mock import MagicMock

import pytest

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.action_type import ActionType
from xp.models.telegram.output_telegram import OutputTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_output_service import TelegramOutputService

SEND_ACTION_OUTPUT_NUMBER = 10
SEND_ACTION_TIMEOUT_SECONDS = 3.0
UPDATED_TIMEOUT_SECONDS = 10.0
SUCCEED_OUTPUT_NUMBER = 7


@pytest.fixture
def mock_conbus_protocol() -> MagicMock:
    """Create a mock ConbusEventProtocol.

    Returns:
        A mock ConbusEventProtocol.

    """
    protocol = MagicMock(spec=ConbusEventProtocol)
    protocol.timeout_seconds = 5.0
    return protocol


@pytest.fixture
def mock_telegram_output_service() -> MagicMock:
    """Create a mock TelegramOutputService.

    Returns:
        A mock TelegramOutputService.

    """
    return MagicMock(spec=TelegramOutputService)


@pytest.fixture
def conbus_output_service(
    mock_conbus_protocol: MagicMock, mock_telegram_output_service: MagicMock
) -> ConbusOutputService:
    """Create a ConbusOutputService instance for testing.

    Returns:
        A ConbusOutputService instance for testing.

    """
    return ConbusOutputService(
        conbus_protocol=mock_conbus_protocol,
        telegram_output_service=mock_telegram_output_service,
    )


def test_init_connects_signals(
    mock_conbus_protocol: MagicMock, mock_telegram_output_service: MagicMock
) -> None:
    """Test that __init__ connects all protocol signals."""
    _ = ConbusOutputService(
        conbus_protocol=mock_conbus_protocol,
        telegram_output_service=mock_telegram_output_service,
    )

    # Verify all signals are connected
    mock_conbus_protocol.on_connection_made.connect.assert_called_once()
    mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
    mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
    mock_conbus_protocol.on_timeout.connect.assert_called_once()
    mock_conbus_protocol.on_failed.connect.assert_called_once()


def test_connection_made_sends_telegram(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that connection_made sends action telegram."""
    conbus_output_service.serial_number = "0012345678"
    conbus_output_service.output_number = 5
    conbus_output_service.action_type = ActionType.ON_RELEASE

    conbus_output_service.connection_made()

    mock_conbus_protocol.send_telegram.assert_called_once_with(
        telegram_type=TelegramType.SYSTEM,
        serial_number="0012345678",
        system_function=SystemFunction.ACTION,
        data_value="05AB",
    )


def test_telegram_sent_updates_response(
    conbus_output_service: ConbusOutputService,
) -> None:
    """Test that telegram_sent updates service response."""
    telegram = "test_telegram"

    conbus_output_service.telegram_sent(telegram)

    assert conbus_output_service.service_response.sent_telegram == telegram


def test_telegram_received_appends_to_list(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that telegram_received appends to received_telegrams list."""
    event = TelegramReceivedEvent(
        protocol=mock_conbus_protocol,
        frame="test_frame",
        telegram="test_telegram",
        telegram_type=TelegramType.REPLY.value,
        serial_number="0012345678",
        payload="test_payload",
        checksum="00",
        checksum_valid=True,
    )

    conbus_output_service.telegram_received(event)

    assert conbus_output_service.service_response.received_telegrams == ["test_frame"]


def test_telegram_received_processes_ack(
    conbus_output_service: ConbusOutputService,
    mock_telegram_output_service: MagicMock,
    mock_conbus_protocol: MagicMock,
) -> None:
    """Test that telegram_received processes ACK response."""
    conbus_output_service.serial_number = "0012345678"
    output_telegram = OutputTelegram(
        serial_number="0012345678",
        system_function=SystemFunction.ACK,
        checksum="00",
        raw_telegram="<S0012345678F16D>",
    )
    mock_telegram_output_service.parse_reply_telegram.return_value = output_telegram

    event = TelegramReceivedEvent(
        protocol=mock_conbus_protocol,
        frame="test_frame",
        telegram="test_telegram",
        telegram_type=TelegramType.REPLY.value,
        serial_number="0012345678",
        payload="test_payload",
        checksum="00",
        checksum_valid=True,
    )

    # Track signal emission
    signal_emitted: list = []
    conbus_output_service.on_finish.connect(signal_emitted.append)

    conbus_output_service.telegram_received(event)

    # Verify ACK was processed
    assert len(signal_emitted) == 1
    assert signal_emitted[0].success is True


def test_timeout_calls_failed(conbus_output_service: ConbusOutputService) -> None:
    """Test that timeout calls failed with timeout message."""
    # Track signal emission
    signal_emitted: list = []
    conbus_output_service.on_finish.connect(signal_emitted.append)

    conbus_output_service.timeout()

    # Verify failed was called with timeout message
    assert len(signal_emitted) == 1
    assert signal_emitted[0].success is False
    assert signal_emitted[0].error == "Timeout"


def test_failed_emits_signal(conbus_output_service: ConbusOutputService) -> None:
    """Test that failed emits on_finish signal."""
    # Track signal emission
    signal_emitted: list = []
    conbus_output_service.on_finish.connect(signal_emitted.append)

    conbus_output_service.failed("Test error")

    # Verify signal was emitted with error
    assert len(signal_emitted) == 1
    assert signal_emitted[0].success is False
    assert signal_emitted[0].error == "Test error"


def test_send_action_sets_state(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that send_action sets service state."""
    conbus_output_service.send_action(
        serial_number="0012345678",
        output_number=SEND_ACTION_OUTPUT_NUMBER,
        action_type=ActionType.OFF_PRESS,
        timeout_seconds=SEND_ACTION_TIMEOUT_SECONDS,
    )

    assert conbus_output_service.serial_number == "0012345678"
    assert conbus_output_service.output_number == SEND_ACTION_OUTPUT_NUMBER
    assert conbus_output_service.action_type == ActionType.OFF_PRESS
    assert mock_conbus_protocol.timeout_seconds == SEND_ACTION_TIMEOUT_SECONDS


def test_set_timeout_delegates_to_protocol(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that set_timeout delegates to protocol."""
    conbus_output_service.set_timeout(UPDATED_TIMEOUT_SECONDS)

    assert mock_conbus_protocol.timeout_seconds == UPDATED_TIMEOUT_SECONDS


def test_start_reactor_delegates_to_protocol(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that start_reactor delegates to protocol."""
    conbus_output_service.start_reactor()

    mock_conbus_protocol.start_reactor.assert_called_once()


def test_stop_reactor_delegates_to_protocol(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that stop_reactor delegates to protocol."""
    conbus_output_service.stop_reactor()

    mock_conbus_protocol.stop_reactor.assert_called_once()


def test_enter_resets_state(conbus_output_service: ConbusOutputService) -> None:
    """Test that __enter__ resets state for singleton reuse."""
    # Set some state
    conbus_output_service.service_response.success = True
    conbus_output_service.output_state = "test"

    # Enter context
    result = conbus_output_service.__enter__()  # noqa: PLC2801 -- __enter__ under test

    # Verify state reset
    assert result is conbus_output_service
    assert conbus_output_service.service_response.success is False
    assert not conbus_output_service.output_state


def test_exit_disconnects_signals(
    conbus_output_service: ConbusOutputService, mock_conbus_protocol: MagicMock
) -> None:
    """Test that __exit__ disconnects all signals and stops reactor."""
    conbus_output_service.__exit__(None, None, None)

    # Verify protocol signals disconnected
    mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
    mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
    mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
    mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
    mock_conbus_protocol.on_failed.disconnect.assert_called_once()

    # Verify reactor stopped
    mock_conbus_protocol.stop_reactor.assert_called_once()


def test_succeed_emits_signal_with_output_telegram(
    conbus_output_service: ConbusOutputService,
) -> None:
    """Test that succeed emits signal with successful response."""
    conbus_output_service.serial_number = "0012345678"
    conbus_output_service.output_number = SUCCEED_OUTPUT_NUMBER
    conbus_output_service.action_type = ActionType.ON_RELEASE

    output_telegram = OutputTelegram(
        serial_number="0012345678",
        system_function=SystemFunction.ACK,
        checksum="00",
        raw_telegram="<S0012345678F16D>",
    )

    # Track signal emission
    signal_emitted: list = []
    conbus_output_service.on_finish.connect(signal_emitted.append)

    conbus_output_service.succeed(output_telegram)

    # Verify signal was emitted with success
    assert len(signal_emitted) == 1
    assert signal_emitted[0].success is True
    assert signal_emitted[0].serial_number == "0012345678"
    assert signal_emitted[0].output_number == SUCCEED_OUTPUT_NUMBER
    assert signal_emitted[0].action_type == ActionType.ON_RELEASE
    assert signal_emitted[0].output_telegram == output_telegram
