"""Unit tests for MsActionTableService."""

from unittest.mock import Mock

import pytest

from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.models.actiontable.msactiontable_xp24 import InputAction as Xp24InputAction
from xp.models.actiontable.msactiontable_xp24 import (
    Xp24MsActionTable,
)
from xp.models.actiontable.msactiontable_xp33 import Xp33MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.msactiontable_service import (
    MsActionTableError,
    MsActionTableService,
)


class TestMsActionTableService:
    """Test cases for MsActionTableService."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

        mock = Mock(spec=ConbusEventProtocol)
        mock.on_connection_made = Mock()
        mock.on_connection_made.connect = Mock()
        mock.on_telegram_sent = Mock()
        mock.on_telegram_sent.connect = Mock()
        mock.on_telegram_received = Mock()
        mock.on_telegram_received.connect = Mock()
        mock.on_timeout = Mock()
        mock.on_timeout.connect = Mock()
        mock.on_failed = Mock()
        mock.on_failed.connect = Mock()
        return mock

    @pytest.fixture
    def mock_xp20_serializer(self):
        """Create mock XP20 serializer."""
        return Mock()

    @pytest.fixture
    def mock_xp24_serializer(self):
        """Create mock XP24 serializer."""
        return Mock()

    @pytest.fixture
    def mock_xp33_serializer(self):
        """Create mock XP33 serializer."""
        return Mock()

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol,
        mock_xp20_serializer,
        mock_xp24_serializer,
        mock_xp33_serializer,
        mock_telegram_service,
    ):
        """Create service instance for testing."""
        return MsActionTableService(
            conbus_protocol=mock_conbus_protocol,
            xp20ms_serializer=mock_xp20_serializer,
            xp24ms_serializer=mock_xp24_serializer,
            xp33ms_serializer=mock_xp33_serializer,
            telegram_service=mock_telegram_service,
        )

    @pytest.fixture
    def sample_xp24_msactiontable(self):
        """Create sample XP24 MsActionTable for testing."""
        return Xp24MsActionTable(
            input1_action=Xp24InputAction(InputActionType.TOGGLE, TimeParam.NONE),
            input2_action=Xp24InputAction(InputActionType.ON, TimeParam.T5SEC),
            input3_action=Xp24InputAction(InputActionType.LEVELSET, TimeParam.T5MIN),
            input4_action=Xp24InputAction(InputActionType.SCENESET, TimeParam.T2MIN),
            mutex12=True,
            mutex34=False,
            mutual_deadtime=Xp24MsActionTable.MS500,
            curtain12=False,
            curtain34=True,
        )

    @pytest.fixture
    def sample_xp20_msactiontable(self):
        """Create sample XP20 MsActionTable for testing."""
        return Xp20MsActionTable()

    @pytest.fixture
    def sample_xp33_msactiontable(self):
        """Create sample XP33 MsActionTable for testing."""
        return Xp33MsActionTable()

    def test_service_initialization(
        self,
        mock_conbus_protocol,
        mock_xp20_serializer,
        mock_xp24_serializer,
        mock_xp33_serializer,
        mock_telegram_service,
    ):
        """Test service can be initialized with required dependencies."""
        service = MsActionTableService(
            conbus_protocol=mock_conbus_protocol,
            xp20ms_serializer=mock_xp20_serializer,
            xp24ms_serializer=mock_xp24_serializer,
            xp33ms_serializer=mock_xp33_serializer,
            telegram_service=mock_telegram_service,
        )

        assert service.conbus_protocol == mock_conbus_protocol
        assert service.xp20ms_serializer == mock_xp20_serializer
        assert service.xp24ms_serializer == mock_xp24_serializer
        assert service.xp33ms_serializer == mock_xp33_serializer
        assert service.telegram_service == mock_telegram_service
        assert service.serial_number == ""
        assert service.xpmoduletype == ""
        assert service.msactiontable_data == []

    def test_connection_made(self, service):
        """Test connection_made sends DOWNLOAD_MSACTIONTABLE telegram."""
        service.serial_number = "0123450001"

        service.connection_made()

        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.DOWNLOAD_MSACTIONTABLE,
            data_value="00",
        )

    def test_telegram_received_msactiontable_data(
        self, service, sample_xp24_msactiontable
    ):
        """Test receiving MSACTIONTABLE telegram appends data and sends ACK."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        mock_progress = Mock()
        service.on_progress.connect(mock_progress)

        # Create mock telegram received event
        telegram_event = TelegramReceivedEvent(
            protocol=service.conbus_protocol,
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
        mock_reply.system_function = SystemFunction.MSACTIONTABLE
        mock_reply.data = "XX"
        mock_reply.data_value = "AAAAACAAAABAAAAC"
        service.telegram_service.parse_reply_telegram.return_value = mock_reply

        service.telegram_received(telegram_event)

        # Should append both data and data_value
        assert service.msactiontable_data == ["XX", "AAAAACAAAABAAAAC"]

        # Should call progress callback via signal
        mock_progress.assert_called_once_with(".")

        # Should send ACK
        service.conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0123450001",
            system_function=SystemFunction.ACK,
            data_value="00",
        )

    def test_telegram_received_eof(self, service, sample_xp24_msactiontable):
        """Test receiving EOF telegram deserializes and emits finish signal."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.system_function import SystemFunction
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"
        service.xpmoduletype = "xp24"
        service.serializer = service.xp24ms_serializer
        service.msactiontable_data = ["AAAAACAAAABAAAAC"]

        mock_finish = Mock()
        service.on_finish.connect(mock_finish)

        # Mock serializer to return sample msactiontable
        service.serializer.from_data.return_value = sample_xp24_msactiontable

        # Create mock telegram received event
        telegram_event = TelegramReceivedEvent(
            protocol=service.conbus_protocol,
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
        service.serializer.from_data.assert_called_once_with("AAAAACAAAABAAAAC")

        # Should emit finish signal with msactiontable
        mock_finish.assert_called_once_with(sample_xp24_msactiontable)

    def test_telegram_received_invalid_checksum(self, service):
        """Test telegram with invalid checksum is ignored."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"

        telegram_event = TelegramReceivedEvent(
            protocol=service.conbus_protocol,
            frame="<R0123450001F17DINVALIDFK>",
            telegram="R0123450001F17DINVALIDFK",
            payload="R0123450001F17DINVALID",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0123450001",
            checksum="FK",
            checksum_valid=False,  # Invalid checksum
        )

        service.telegram_received(telegram_event)

        # Should not process the telegram
        assert service.msactiontable_data == []
        service.conbus_protocol.send_telegram.assert_not_called()

    def test_telegram_received_wrong_serial(self, service):
        """Test telegram for different serial number is ignored."""
        from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
        from xp.models.telegram.telegram_type import TelegramType

        service.serial_number = "0123450001"

        telegram_event = TelegramReceivedEvent(
            protocol=service.conbus_protocol,
            frame="<R9999999999F17DXXAAAAACFK>",
            telegram="R9999999999F17DXXAAAAACFK",
            payload="R9999999999F17DXXAAAAAC",
            telegram_type=TelegramType.REPLY.value,
            serial_number="9999999999",  # Different serial
            checksum="FK",
            checksum_valid=True,
        )

        service.telegram_received(telegram_event)

        # Should not process the telegram
        assert service.msactiontable_data == []
        service.conbus_protocol.send_telegram.assert_not_called()

    def test_failed_emits_signals(self, service):
        """Test failed method emits error and finish signals."""
        mock_error = Mock()
        mock_finish = Mock()
        service.on_error.connect(mock_error)
        service.on_finish.connect(mock_finish)

        service.failed("Connection timeout")

        mock_error.assert_called_once_with("Connection timeout")
        mock_finish.assert_called_once_with(None)

    def test_start_method_xp24(self, service):
        """Test start method with xp24 module type."""
        service.start(
            serial_number="0123450001",
            xpmoduletype="xp24",
            timeout_seconds=10.0,
        )

        assert service.serial_number == "0123450001"
        assert service.xpmoduletype == "xp24"
        assert service.serializer == service.xp24ms_serializer
        assert service.conbus_protocol.timeout_seconds == 10.0

    def test_start_method_xp20(self, service):
        """Test start method with xp20 module type."""
        service.start(
            serial_number="0123450001",
            xpmoduletype="xp20",
        )

        assert service.xpmoduletype == "xp20"
        assert service.serializer == service.xp20ms_serializer

    def test_start_method_xp33(self, service):
        """Test start method with xp33 module type."""
        service.start(
            serial_number="0123450001",
            xpmoduletype="xp33",
        )

        assert service.xpmoduletype == "xp33"
        assert service.serializer == service.xp33ms_serializer

    def test_start_method_invalid_module_type(self, service):
        """Test start method with invalid module type raises error."""
        with pytest.raises(MsActionTableError, match="Unsupported module type: xp99"):
            service.start(
                serial_number="0123450001",
                xpmoduletype="xp99",
            )

    def test_context_manager(self, service):
        """Test service works as context manager."""
        with service as ctx_service:
            assert ctx_service is service
