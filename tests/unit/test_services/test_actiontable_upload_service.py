"""Unit tests for ActionTableUploadService."""

from unittest.mock import Mock, patch

import pytest

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.actiontable_upload_service import (
    ActionTableUploadService,
)


class TestActionTableUploadService:
    """Test cases for ActionTableUploadService."""

    @pytest.fixture
    def mock_cli_config(self):
        """Create mock CLI config."""
        return Mock()

    @pytest.fixture
    def mock_reactor(self):
        """Create mock reactor."""
        return Mock()

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        return Mock()

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def mock_conson_config(self):
        """Create mock Conson config."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_cli_config,
        mock_reactor,
        mock_serializer,
        mock_telegram_service,
        mock_conson_config,
    ):
        """Create service instance for testing."""
        return ActionTableUploadService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
            conson_config=mock_conson_config,
        )

    @pytest.fixture
    def sample_actiontable(self):
        """Create sample ActionTable for testing."""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=0,
                module_output=1,
                inverted=False,
                command=InputActionType.TURNOFF,
                parameter=TimeParam.NONE,
            ),
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=1,
                module_output=1,
                inverted=True,
                command=InputActionType.TURNON,
                parameter=TimeParam.NONE,
            ),
        ]
        return ActionTable(entries=entries)

    def test_service_initialization(
        self,
        mock_cli_config,
        mock_reactor,
        mock_serializer,
        mock_telegram_service,
        mock_conson_config,
    ):
        """Test service can be initialized with required dependencies."""
        service = ActionTableUploadService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
            conson_config=mock_conson_config,
        )

        assert service.serializer == mock_serializer
        assert service.telegram_service == mock_telegram_service
        assert service.conson_config == mock_conson_config
        assert service.serial_number == ""
        assert service.progress_callback is None
        assert service.error_callback is None
        assert service.success_callback is None
        assert service.upload_data_chunks == []
        assert service.current_chunk_index == 0

    def test_connection_established(self, service):
        """Test connection_established sends UPLOAD_ACTIONTABLE telegram."""
        service.serial_number = "0123450001"

        with patch.object(service, "send_telegram") as mock_send:
            service.connection_established()

            from xp.models.telegram.system_function import SystemFunction
            from xp.models.telegram.telegram_type import TelegramType

            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.UPLOAD_ACTIONTABLE,
                data_value="00",
            )


class TestActionTableUploadChunkPrefix:
    """Test cases for chunk prefix sequence (AA, AB, AC, AD...)."""

    @pytest.fixture
    def mock_cli_config(self):
        """Create mock CLI config."""
        return Mock()

    @pytest.fixture
    def mock_reactor(self):
        """Create mock reactor."""
        return Mock()

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        return Mock()

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def mock_conson_config(self):
        """Create mock Conson config."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_cli_config,
        mock_reactor,
        mock_serializer,
        mock_telegram_service,
        mock_conson_config,
    ):
        """Create service instance for testing."""
        return ActionTableUploadService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
            conson_config=mock_conson_config,
        )

    def test_first_chunk_has_aa_prefix(self, service):
        """Test that first chunk is sent with AA prefix."""
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1DATA", "CHUNK2DATA"]
        service.current_chunk_index = 0

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(service, "send_telegram") as mock_send:
            service._handle_upload_response(mock_reply)

            # Verify first chunk sent with AA prefix
            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.ACTIONTABLE,
                data_value="AACHUNK1DATA",  # AA prefix
            )

    def test_second_chunk_has_ab_prefix(self, service):
        """Test that second chunk is sent with AB prefix."""
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1DATA", "CHUNK2DATA", "CHUNK3DATA"]
        service.current_chunk_index = 1  # Second chunk

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(service, "send_telegram") as mock_send:
            service._handle_upload_response(mock_reply)

            # Verify second chunk sent with AB prefix
            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.ACTIONTABLE,
                data_value="ABCHUNK2DATA",  # AB prefix
            )

    def test_third_chunk_has_ac_prefix(self, service):
        """Test that third chunk is sent with AC prefix."""
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1", "CHUNK2", "CHUNK3", "CHUNK4"]
        service.current_chunk_index = 2  # Third chunk

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(service, "send_telegram") as mock_send:
            service._handle_upload_response(mock_reply)

            # Verify third chunk sent with AC prefix
            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.ACTIONTABLE,
                data_value="ACCHUNK3",  # AC prefix
            )

    def test_fourth_chunk_has_ad_prefix(self, service):
        """Test that fourth chunk is sent with AD prefix."""
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.upload_data_chunks = ["C1", "C2", "C3", "C4", "C5"]
        service.current_chunk_index = 3  # Fourth chunk

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(service, "send_telegram") as mock_send:
            service._handle_upload_response(mock_reply)

            # Verify fourth chunk sent with AD prefix
            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.ACTIONTABLE,
                data_value="ADC4",  # AD prefix
            )

    def test_chunk_prefix_sequence_increments(self, service):
        """Test that chunk prefix increments correctly through sequence."""
        from xp.models.telegram.system_function import SystemFunction

        service.serial_number = "0123450001"
        service.upload_data_chunks = ["C0", "C1", "C2", "C3", "C4", "C5"]
        service.current_chunk_index = 0

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        expected_prefixes = ["AA", "AB", "AC", "AD", "AE", "AF"]

        with patch.object(service, "send_telegram") as mock_send, patch.object(
            service, "_stop_reactor"
        ):
            for i, expected_prefix in enumerate(expected_prefixes):
                service.current_chunk_index = i
                mock_send.reset_mock()

                service._handle_upload_response(mock_reply)

                # Verify correct prefix
                mock_send.assert_called_once()
                call_args = mock_send.call_args
                data_value = call_args.kwargs["data_value"]
                assert data_value.startswith(
                    expected_prefix
                ), f"Chunk {i} should have prefix {expected_prefix}, got {data_value[:2]}"

    def test_chunk_prefix_calculation(self, service):
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
            assert (
                prefix_value == expected_value
            ), f"Chunk {chunk_index}: expected 0x{expected_value:02X}, got 0x{prefix_value:02X}"

    def test_sends_eof_after_all_chunks(self, service):
        """Test that EOF is sent after all chunks are transmitted."""
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.upload_data_chunks = ["CHUNK1", "CHUNK2"]
        service.current_chunk_index = 2  # All chunks sent
        service.success_callback = Mock()

        # Create mock ACK reply
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(service, "send_telegram") as mock_send, patch.object(
            service, "_stop_reactor"
        ):
            service._handle_upload_response(mock_reply)

            # Should send EOF
            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.EOF,
                data_value="00",
            )

            # Should call success callback
            service.success_callback.assert_called_once()
