"""Unit tests for ActionTableService."""

from unittest.mock import Mock, patch

import pytest

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.actiontable.actiontable_type import ActionTableType
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
)


class TestActionTableService:
    """Test cases for ActionTableService."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        protocol = Mock()
        protocol.on_connection_made = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_timeout = Mock()
        protocol.on_failed = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed.disconnect = Mock()
        return protocol

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        return Mock()

    @pytest.fixture
    def service(self, mock_conbus_protocol, mock_serializer):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
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

    def test_service_initialization(self, mock_conbus_protocol, mock_serializer):
        """Test service can be initialized with required dependencies."""
        service = ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
        )

        assert service.conbus_protocol == mock_conbus_protocol
        assert service.actiontable_serializer == mock_serializer
        assert service.serial_number == ""
        assert hasattr(service, "on_progress")
        assert hasattr(service, "on_error")
        assert hasattr(service, "on_finish")
        assert service.actiontable_data == []

    def test_connection_made(self, service):
        """Test _on_connection_made transitions to receiving state."""
        service.serial_number = "0123450001"

        service._on_connection_made()

        # Should be in receiving state after connection
        assert service.receiving.is_active

    def test_telegram_received_actiontable_data(self, service, sample_actiontable):
        """Test receiving ACTIONTABLE telegram appends data and sends ACK."""
        from xp.models.telegram.system_function import SystemFunction

        service.serial_number = "0123450001"
        mock_progress = Mock()
        service.on_progress.connect(mock_progress)

        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()
        assert service.waiting_data.is_active

        # Create mock reply telegram
        mock_reply = Mock()
        mock_reply.serial_number = "0123450001"
        mock_reply.system_function = SystemFunction.ACTIONTABLE
        mock_reply.data_value = "XXAAAAACAAAABAAAAC"
        actiontable_chunk = "AAAAACAAAABAAAAC"  # Chunk data (data_value minus header)

        with patch.object(service.conbus_protocol, "send_ack") as mock_send_ack:
            # Call the actiontable chunk handler directly (protocol now parses and emits)
            service._on_actiontable_chunk_received(mock_reply, actiontable_chunk)

            # Should append chunk data
            assert service.actiontable_data == ["AAAAACAAAABAAAAC"]

            # Should call progress callback
            mock_progress.assert_called_once_with(".")

            # Should send ACK (on_enter_receiving_chunk)
            mock_send_ack.assert_called_once_with(
                serial_number="0123450001",
            )

    def test_telegram_received_eof(self, service, sample_actiontable):
        """Test receiving EOF telegram deserializes and calls finish_callback."""
        from xp.models.telegram.system_function import SystemFunction

        service.serial_number = "0123450001"
        service.actiontable_data = ["AAAAACAAAABAAAAC"]

        mock_actiontable_received = Mock()
        service.on_actiontable_received.connect(mock_actiontable_received)

        # Mock serializer to return sample actiontable
        service.actiontable_serializer.from_encoded_string.return_value = (
            sample_actiontable
        )
        service.actiontable_serializer.to_short_string.return_value = [
            "CP20 0 0 > 1 OFF;",
            "CP20 0 1 > 1 ~ON;",
        ]

        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()
        assert service.waiting_data.is_active

        # Create mock reply telegram
        mock_reply = Mock()
        mock_reply.serial_number = "0123450001"
        mock_reply.system_function = SystemFunction.EOF

        # Call the EOF handler directly (protocol now parses and emits)
        service._on_eof_received(mock_reply)

        # Should deserialize all collected data
        service.actiontable_serializer.from_encoded_string.assert_called_once_with(
            "AAAAACAAAABAAAAC"
        )

        # Should call on_actiontable_received with actiontable and short format
        expected_short = ["CP20 0 0 > 1 OFF;", "CP20 0 1 > 1 ~ON;"]
        mock_actiontable_received.assert_called_once_with(
            sample_actiontable, expected_short
        )

    def test_telegram_received_invalid_checksum(self, service):
        """Test telegram with invalid checksum is ignored."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"

        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=service.conbus_protocol,
            frame="<R0123450001F17DINVALIDFK>",
            telegram="R0123450001F17DINVALIDFK",
            payload="R0123450001F17DINVALID",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0123450001",
            checksum="FK",
            checksum_valid=False,  # Invalid checksum
        )

        with patch.object(service.conbus_protocol, "send_telegram") as mock_send:
            service._on_telegram_received(telegram_event)

            # Should not process the telegram
            assert service.actiontable_data == []
            mock_send.assert_not_called()

    def test_telegram_received_wrong_serial(self, service):
        """Test telegram for different serial number is ignored."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"

        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()

        telegram_event = TelegramReceivedEvent.model_construct(
            protocol=service.conbus_protocol,
            frame="<R9999999999F17DXXAAAAACFK>",
            telegram="R9999999999F17DXXAAAAACFK",
            payload="R9999999999F17DXXAAAAAC",
            telegram_type=TelegramType.REPLY.value,
            serial_number="9999999999",  # Different serial
            checksum="FK",
            checksum_valid=True,
        )

        with patch.object(service.conbus_protocol, "send_telegram") as mock_send:
            service._on_telegram_received(telegram_event)

            # Should not process the telegram
            assert service.actiontable_data == []
            mock_send.assert_not_called()

    def test_failed_callback(self, service):
        """Test _on_failed method calls error_callback."""
        mock_error = Mock()
        service.on_error.connect(mock_error)

        service._on_failed("Connection timeout")

        mock_error.assert_called_once_with("Connection timeout")

    def test_start_method(self, service):
        """Test start method sets up serial number and timeout."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.ACTIONTABLE,
            timeout_seconds=10.0,
        )

        assert service.serial_number == "0123450001"
        assert service.conbus_protocol.timeout_seconds == 10.0

    def test_context_manager(self, service):
        """Test service works as context manager."""
        with service as ctx_service:
            assert ctx_service is service
