"""Unit tests for ActionTableService."""

from unittest.mock import Mock, patch

import pytest

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableService,
)


class TestActionTableService:
    """Test cases for ActionTableService."""

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
    def service(
        self, mock_cli_config, mock_reactor, mock_serializer, mock_telegram_service
    ):
        """Create service instance for testing."""
        return ActionTableService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
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

    def test_service_initialization(
        self, mock_cli_config, mock_reactor, mock_serializer, mock_telegram_service
    ):
        """Test service can be initialized with required dependencies."""
        service = ActionTableService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
        )

        assert service.serializer == mock_serializer
        assert service.telegram_service == mock_telegram_service
        assert service.serial_number == ""
        assert service.progress_callback is None
        assert service.error_callback is None
        assert service.finish_callback is None
        assert service.actiontable_data == []

    def test_connection_established(self, service):
        """Test connection_established sends DOWNLOAD_ACTIONTABLE telegram."""
        service.serial_number = "0123450001"

        with patch.object(service, "send_telegram") as mock_send:
            service.connection_established()

            from xp.models.telegram.system_function import SystemFunction
            from xp.models.telegram.telegram_type import TelegramType

            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.DOWNLOAD_ACTIONTABLE,
                data_value="00",
            )

    def test_telegram_received_actiontable_data(self, service, sample_actiontable):
        """Test receiving ACTIONTABLE telegram appends data and sends ACK."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        mock_progress = Mock()
        service.progress_callback = mock_progress

        # Create mock telegram received event
        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0123450001F17DXXAAAAACAAAABAAAACFK>",
            telegram="R0123450001F17DXXAAAAACAAAABAAAACFK",
            payload="R0123450001F17DXXAAAAACAAAABAAAAC",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0123450001",
            checksum="FK",
            checksum_valid=True,
        )

        # Mock the reply telegram parsing
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACTIONTABLE
        mock_reply.data_value = "XXAAAAACAAAABAAAAC"
        service.telegram_service.parse_reply_telegram.return_value = mock_reply

        with patch.object(service, "send_telegram") as mock_send:
            service.telegram_received(telegram_event)

            # Should append data (without first 2 chars)
            assert service.actiontable_data == ["AAAAACAAAABAAAAC"]

            # Should call progress callback
            mock_progress.assert_called_once_with(".")

            # Should send ACK
            mock_send.assert_called_once_with(
                telegram_type=TelegramType.SYSTEM,
                serial_number="0123450001",
                system_function=SystemFunction.ACK,
                data_value="00",
            )

    def test_telegram_received_eof(self, service, sample_actiontable):
        """Test receiving EOF telegram deserializes and calls finish_callback."""
        from dataclasses import asdict

        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.actiontable_data = ["AAAAACAAAABAAAAC"]

        mock_finish = Mock()
        service.finish_callback = mock_finish

        # Mock serializer to return sample actiontable
        service.serializer.from_encoded_string.return_value = sample_actiontable
        service.serializer.format_decoded_output.return_value = [
            "CP20 0 0 > 1 OFF;",
            "CP20 0 1 > 1 ~ON;",
        ]

        # Create mock telegram received event
        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0123450001F16DEO>",
            telegram="R0123450001F16DEO",
            payload="R0123450001F16D",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0123450001",
            checksum="EO",
            checksum_valid=True,
        )

        # Mock the reply telegram parsing
        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.EOF
        service.telegram_service.parse_reply_telegram.return_value = mock_reply

        service.telegram_received(telegram_event)

        # Should deserialize all collected data
        service.serializer.from_encoded_string.assert_called_once_with(
            "AAAAACAAAABAAAAC"
        )

        # Should call finish callback with actiontable, dict, and short format
        expected_dict = asdict(sample_actiontable)
        expected_short = ["CP20 0 0 > 1 OFF;", "CP20 0 1 > 1 ~ON;"]
        mock_finish.assert_called_once_with(
            sample_actiontable, expected_dict, expected_short
        )

    def test_telegram_received_invalid_checksum(self, service):
        """Test telegram with invalid checksum is ignored."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"

        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R0123450001F17DINVALIDFK>",
            telegram="R0123450001F17DINVALIDFK",
            payload="R0123450001F17DINVALID",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0123450001",
            checksum="FK",
            checksum_valid=False,  # Invalid checksum
        )

        with patch.object(service, "send_telegram") as mock_send:
            service.telegram_received(telegram_event)

            # Should not process the telegram
            assert service.actiontable_data == []
            mock_send.assert_not_called()

    def test_telegram_received_wrong_serial(self, service):
        """Test telegram for different serial number is ignored."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"

        telegram_event = TelegramReceivedEvent(
            protocol=service,
            frame="<R9999999999F17DXXAAAAACFK>",
            telegram="R9999999999F17DXXAAAAACFK",
            payload="R9999999999F17DXXAAAAAC",
            telegram_type=TelegramType.REPLY.value,
            serial_number="9999999999",  # Different serial
            checksum="FK",
            checksum_valid=True,
        )

        with patch.object(service, "send_telegram") as mock_send:
            service.telegram_received(telegram_event)

            # Should not process the telegram
            assert service.actiontable_data == []
            mock_send.assert_not_called()

    def test_failed_callback(self, service):
        """Test failed method calls error_callback."""
        mock_error = Mock()
        service.error_callback = mock_error

        service.failed("Connection timeout")

        mock_error.assert_called_once_with("Connection timeout")

    def test_start_method(self, service):
        """Test start method sets up callbacks and starts reactor."""
        mock_progress = Mock()
        mock_error = Mock()
        mock_finish = Mock()

        with patch.object(service, "start_reactor") as mock_start_reactor:
            service.start(
                serial_number="0123450001",
                progress_callback=mock_progress,
                error_callback=mock_error,
                finish_callback=mock_finish,
                timeout_seconds=10.0,
            )

            assert service.serial_number == "0123450001"
            assert service.progress_callback == mock_progress
            assert service.error_callback == mock_error
            assert service.finish_callback == mock_finish
            assert service.timeout_seconds == 10.0
            mock_start_reactor.assert_called_once()

    def test_context_manager(self, service):
        """Test service works as context manager."""
        with service as ctx_service:
            assert ctx_service is service
