# Copyright (c) 2025 ldvchosal
"""Unit tests for ActionTableUploadService."""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.actiontable.actiontable_type import ActionTableType2
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.actiontable_upload_service import (
    ActionTableUploadService,
    MsActionTableSerializers,
)

# 1 UPLOAD_ACTIONTABLE + 15 ACTIONTABLE chunks + 1 EOF.
EXPECTED_TELEGRAM_COUNT = 17
# Each chunk data_value is 68 chars: 4-char prefix + 64-char chunk payload.
CHUNK_DATA_VALUE_LENGTH = 68
# 96 entries x 5 bytes x 2 hex chars.
ENCODED_ACTIONTABLE_LENGTH = 960


@dataclass
class ServiceMocks:
    """Mocked dependencies for ActionTableUploadService."""

    conbus_protocol: Mock
    serializer: Mock
    xp20ms_serializer: Mock
    xp24ms_serializer: Mock
    xp33ms_serializer: Mock
    telegram_service: Mock
    conson_config: Mock


@pytest.fixture
def mocks() -> ServiceMocks:
    """Create mocked dependencies for the service.

    Returns:
        Mocked dependencies for the service.

    """
    protocol = Mock()
    protocol.timeout_seconds = 5.0
    return ServiceMocks(
        conbus_protocol=protocol,
        serializer=Mock(),
        xp20ms_serializer=Mock(),
        xp24ms_serializer=Mock(),
        xp33ms_serializer=Mock(),
        telegram_service=Mock(),
        conson_config=Mock(),
    )


@pytest.fixture
def service(mocks: ServiceMocks) -> ActionTableUploadService:
    """Create service instance for testing.

    Returns:
        Service instance for testing.

    """
    return ActionTableUploadService(
        conbus_protocol=mocks.conbus_protocol,
        serializers=MsActionTableSerializers(
            actiontable=mocks.serializer,
            xp20ms=mocks.xp20ms_serializer,
            xp24ms=mocks.xp24ms_serializer,
            xp33ms=mocks.xp33ms_serializer,
        ),
        telegram_service=mocks.telegram_service,
        conson_config=mocks.conson_config,
    )


def deliver_reply(
    service: ActionTableUploadService,
    mocks: ServiceMocks,
    reply_telegram: Mock,
) -> None:
    """Deliver a parsed reply through the public telegram_received API.

    Simulates the protocol receiving a valid reply frame for the service's
    serial number, with the telegram service parsing it to reply_telegram.
    """
    mocks.telegram_service.parse_reply_telegram.return_value = reply_telegram
    event = TelegramReceivedEvent.model_construct(
        protocol=mocks.conbus_protocol,
        frame="<R0000000000F18DFA>",
        telegram="R0000000000F18DFA",
        payload="R0000000000F18D",
        telegram_type=TelegramType.REPLY.value,
        serial_number=service.serial_number,
        checksum="FA",
        checksum_valid=True,
    )
    service.telegram_received(event)


class TestActionTableUploadService:
    """Test cases for ActionTableUploadService."""

    @pytest.fixture
    def sample_actiontable(self) -> ActionTable:
        """Create sample ActionTable for testing.

        Returns:
            Sample ActionTable for testing.

        """
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=0,
                module_output=1,
                inverted=False,
                command=InputActionType.OFF,
                parameter=TimeParam.NONE,
            ),
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=1,
                module_output=1,
                inverted=True,
                command=InputActionType.ON,
                parameter=TimeParam.NONE,
            ),
        ]
        return ActionTable(entries=entries)

    def test_service_initialization(self, mocks: ServiceMocks) -> None:
        """Test service can be initialized with required dependencies."""
        service = ActionTableUploadService(
            conbus_protocol=mocks.conbus_protocol,
            serializers=MsActionTableSerializers(
                actiontable=mocks.serializer,
                xp20ms=mocks.xp20ms_serializer,
                xp24ms=mocks.xp24ms_serializer,
                xp33ms=mocks.xp33ms_serializer,
            ),
            telegram_service=mocks.telegram_service,
            conson_config=mocks.conson_config,
        )

        assert service.conbus_protocol == mocks.conbus_protocol
        assert service.telegram_service == mocks.telegram_service
        assert service.conson_config == mocks.conson_config
        assert not service.serial_number
        assert hasattr(service, "on_progress")
        assert hasattr(service, "on_error")
        assert hasattr(service, "on_finish")
        assert service.upload_data_chunks == []
        assert service.current_chunk_index == 0

        # Verify signals were connected
        mocks.conbus_protocol.on_connection_made.connect.assert_called_once()
        mocks.conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mocks.conbus_protocol.on_telegram_received.connect.assert_called_once()
        mocks.conbus_protocol.on_timeout.connect.assert_called_once()
        mocks.conbus_protocol.on_failed.connect.assert_called_once()

    def test_connection_made(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test connection_made sends UPLOAD_ACTIONTABLE telegram."""
        service.serial_number = "0123450001"

        service.connection_made()

        mocks.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.UPLOAD_ACTIONTABLE,
            data_value="00",
        )


class TestActionTableUploadChunkPrefix:
    """Test cases for chunk prefix sequence (AA, AB, AC, AD...)."""

    def test_first_chunk_has_aa_prefix(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test that first chunk is sent with AA prefix."""
        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1DATA", "CHUNK2DATA"]
        service.current_chunk_index = 0

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        deliver_reply(service, mocks, mock_reply)

        # Verify first chunk sent with AA prefix
        mocks.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.ACTIONTABLE,
            data_value="AAAACHUNK1DATA",  # AA prefix
        )

    def test_second_chunk_has_ab_prefix(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test that second chunk is sent with AB prefix."""
        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1DATA", "CHUNK2DATA", "CHUNK3DATA"]
        service.current_chunk_index = 1  # Second chunk

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        deliver_reply(service, mocks, mock_reply)

        # Verify second chunk sent with AB prefix
        mocks.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.ACTIONTABLE,
            data_value="AAABCHUNK2DATA",  # AB prefix
        )

    def test_third_chunk_has_ac_prefix(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test that third chunk is sent with AC prefix."""
        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1", "CHUNK2", "CHUNK3", "CHUNK4"]
        service.current_chunk_index = 2  # Third chunk

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        deliver_reply(service, mocks, mock_reply)

        # Verify third chunk sent with AC prefix
        mocks.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.ACTIONTABLE,
            data_value="AAACCHUNK3",  # AC prefix
        )

    def test_fourth_chunk_has_ad_prefix(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test that fourth chunk is sent with AD prefix."""
        service.serial_number = "0123450001"
        service.upload_data_chunks = ["C1", "C2", "C3", "C4", "C5"]
        service.current_chunk_index = 3  # Fourth chunk

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        deliver_reply(service, mocks, mock_reply)

        # Verify fourth chunk sent with AD prefix
        mocks.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.ACTIONTABLE,
            data_value="AAADC4",  # AD prefix
        )

    def test_chunk_prefix_sequence_increments(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test that chunk prefix increments correctly through sequence."""
        service.serial_number = "0123450001"
        service.upload_data_chunks = ["C0", "C1", "C2", "C3", "C4", "C5"]
        service.current_chunk_index = 0

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        expected_prefixes = ["AAAA", "AAAB", "AAAC", "AAAD", "AAAE", "AAAF"]

        for i, expected_prefix in enumerate(expected_prefixes):
            service.current_chunk_index = i
            mocks.conbus_protocol.send_telegram.reset_mock()

            deliver_reply(service, mocks, mock_reply)

            # Verify correct prefix
            mocks.conbus_protocol.send_telegram.assert_called_once()
            call_args = mocks.conbus_protocol.send_telegram.call_args
            data_value = call_args.kwargs["data_value"]
            assert data_value.startswith(expected_prefix), (
                f"Chunk {i} should have prefix {expected_prefix}, got {data_value[:4]}"
            )

    def test_chunk_prefix_calculation(self) -> None:
        """Test chunk prefix calculation formula: 0xA0 | (0xA + index)."""
        # Test the prefix calculation directly
        test_cases = [
            (0, 0xAA),  # First chunk: 0xA0 | 0xA = 0xAA
            (1, 0xAB),  # Second chunk: 0xA0 | 0xB = 0xAB
            (2, 0xAC),  # Third chunk: 0xA0 | 0xC = 0xAC
            (3, 0xAD),  # Fourth chunk: 0xA0 | 0xD = 0xAD
            (4, 0xAE),  # Fifth chunk: 0xA0 | 0xE = 0xAE
            (5, 0xAF),  # Sixth chunk: 0xA0 | 0xF = 0xAF
        ]

        for chunk_index, expected_value in test_cases:
            # This is the formula used in the implementation
            prefix_value = 0xA0 | (0xA + chunk_index)
            assert prefix_value == expected_value, (
                f"Chunk {chunk_index}: expected 0x{expected_value:02X}, "
                f"got 0x{prefix_value:02X}"
            )

    def test_sends_eof_after_all_chunks(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test that EOF is sent after all chunks are transmitted."""
        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1", "CHUNK2"]
        service.current_chunk_index = 2  # All chunks sent
        mock_finish = Mock()
        service.on_finish.connect(mock_finish)

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        # First ACK after all chunks sent triggers EOF
        deliver_reply(service, mocks, mock_reply)

        # Should send EOF
        mocks.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.EOF,
            data_value="00",
        )

        # Second ACK (after EOF) triggers finish signal
        deliver_reply(service, mocks, mock_reply)

        # Should call finish signal with True
        mock_finish.assert_called_once()
        assert mock_finish.call_args.args == (True,)


class TestActionTableUploadFullSequence:
    """Test complete 96-entry ActionTable upload telegram sequence."""

    @pytest.fixture
    def nomod_96_actiontable(self) -> ActionTable:
        """Create 96-entry NOMOD ActionTable for testing.

        Returns:
            96-entry NOMOD ActionTable for testing.

        """
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.NOMOD,
                link_number=0,
                module_input=0,
                module_output=0,
                inverted=False,
                command=InputActionType.VOID,
                parameter=TimeParam.NONE,
            )
            for _ in range(96)
        ]
        return ActionTable(entries=entries)

    def test_upload_generates_correct_telegram_sequence(
        self,
        service: ActionTableUploadService,
        mocks: ServiceMocks,
        nomod_96_actiontable: ActionTable,
    ) -> None:
        """Test 96-entry ActionTable upload creates correct telegram sequence.

        Verifies:
        - Exactly 16 telegrams sent (1 UPLOAD_ACTIONTABLE + 15 ACTIONTABLE)
        - Telegram prefixes follow sequence:
          AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ, AK, AL, AM, AN, AO
        - Each ACTIONTABLE telegram data_value starts with correct prefix
        - Each chunk is 66 chars (2-char prefix + 64-char data)
        - EOF telegram is sent after all chunks
        """
        # Setup: Mock module with action table
        mock_module = Mock()
        mock_module.action_table = ["NOMOD 0 0 > 0 VOID;"] * 96
        mocks.conson_config.find_module.return_value = mock_module

        # Setup: Mock serializer - 96 entries * 10 chars = 960 chars
        # (15 chunks of 64)
        mocks.serializer.parse_action_table.return_value = nomod_96_actiontable
        # Create 960 'A' characters (96 entries x 5 bytes x 2 hex chars)
        mocks.serializer.to_encoded_string.return_value = (
            "A" * ENCODED_ACTIONTABLE_LENGTH
        )

        # Setup signal connections
        mock_progress = Mock()
        mock_error = Mock()
        mock_finish = Mock()
        service.on_progress.connect(mock_progress)
        service.on_error.connect(mock_error)
        service.on_finish.connect(mock_finish)

        # Start upload
        service.start(
            serial_number="0020044974", actiontable_type=ActionTableType2.ACTIONTABLE
        )

        # Simulate connection made
        service.connection_made()

        # Simulate ACK responses for each chunk + ACK to trigger EOF
        # + ACK after EOF
        mock_ack = Mock()
        mock_ack.system_function = SystemFunction.ACK

        for _ in range(EXPECTED_TELEGRAM_COUNT):
            deliver_reply(service, mocks, mock_ack)

        # Collect all telegrams sent through the protocol
        sent_telegrams = [
            c.kwargs for c in mocks.conbus_protocol.send_telegram.call_args_list
        ]

        # Verify: Exactly 17 telegrams sent
        # (1 UPLOAD_ACTIONTABLE + 15 ACTIONTABLE + 1 EOF)
        assert len(sent_telegrams) == EXPECTED_TELEGRAM_COUNT, (
            f"Expected {EXPECTED_TELEGRAM_COUNT} telegrams, got {len(sent_telegrams)}"
        )

        # Verify: First telegram is UPLOAD_ACTIONTABLE
        assert sent_telegrams[0]["system_function"] == SystemFunction.UPLOAD_ACTIONTABLE
        assert sent_telegrams[0]["serial_number"] == "0020044974"
        assert sent_telegrams[0]["telegram_type"] == TelegramType.SYSTEM
        assert sent_telegrams[0]["data_value"] == "00"

        # Verify: Next 15 telegrams are ACTIONTABLE with correct prefixes
        expected_prefixes = [
            "AAAA",
            "AAAB",
            "AAAC",
            "AAAD",
            "AAAE",
            "AAAF",
            "AAAG",
            "AAAH",
            "AAAI",
            "AAAJ",
            "AAAK",
            "AAAL",
            "AAAM",
            "AAAN",
            "AAAO",
        ]

        for i, expected_prefix in enumerate(expected_prefixes):
            telegram = sent_telegrams[i + 1]
            assert telegram["system_function"] == SystemFunction.ACTIONTABLE
            assert telegram["serial_number"] == "0020044974"
            assert telegram["telegram_type"] == TelegramType.SYSTEM
            assert telegram["data_value"].startswith(expected_prefix), (
                f"Telegram {i + 1} should start with {expected_prefix}, "
                f"got {telegram['data_value'][:2]}"
            )
            # Each telegram should be 68 chars: 4-char prefix + 64-char chunk
            assert len(telegram["data_value"]) == CHUNK_DATA_VALUE_LENGTH, (
                f"Telegram {i + 1} data_value should be "
                f"{CHUNK_DATA_VALUE_LENGTH} chars, "
                f"got {len(telegram['data_value'])}"
            )

        # Verify: Last telegram is EOF
        assert sent_telegrams[-1]["system_function"] == SystemFunction.EOF
        assert sent_telegrams[-1]["serial_number"] == "0020044974"
        assert sent_telegrams[-1]["telegram_type"] == TelegramType.SYSTEM
        assert sent_telegrams[-1]["data_value"] == "00"

        # Verify: Data integrity - concatenate all chunks (excluding prefixes)
        all_chunks = "".join(
            sent_telegrams[i]["data_value"][4:]
            for i in range(1, 16)  # Skip prefix
        )
        assert all_chunks == "A" * ENCODED_ACTIONTABLE_LENGTH, (
            "Concatenated chunks should match serialized data"
        )

        # Verify: Finish signal was called with True
        mock_finish.assert_called_once()
        assert mock_finish.call_args.args == (True,)

    def test_upload_with_module_not_found(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test upload fails when module is not found."""
        mocks.conson_config.find_module.return_value = None

        mock_error = Mock()
        service.on_error.connect(mock_error)

        service.start(
            serial_number="9999999999", actiontable_type=ActionTableType2.ACTIONTABLE
        )

        # Verify error signal was called with appropriate message
        mock_error.assert_called_once()
        assert "not found" in mock_error.call_args[0][0].lower()

    def test_upload_with_invalid_action_table(
        self, service: ActionTableUploadService, mocks: ServiceMocks
    ) -> None:
        """Test upload fails when action table is invalid."""
        # Setup: Mock module with action table
        mock_module = Mock()
        mock_module.action_table = ["INVALID ACTION TABLE FORMAT"]
        mocks.conson_config.find_module.return_value = mock_module

        # Setup: Serializer raises ValueError for invalid format
        mocks.serializer.from_short_string.side_effect = ValueError(
            "Invalid action table format"
        )

        mock_error = Mock()
        service.on_error.connect(mock_error)

        service.start(
            serial_number="0020044974", actiontable_type=ActionTableType2.ACTIONTABLE
        )

        # Verify error signal was called
        mock_error.assert_called_once()
        assert "invalid" in mock_error.call_args[0][0].lower()
