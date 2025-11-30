"""Unit tests for ActionTableDownloadService."""

from unittest.mock import Mock

import pytest

from xp.models.actiontable.actiontable_type import ActionTableType
from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.models.actiontable.msactiontable_xp24 import InputAction as Xp24InputAction
from xp.models.actiontable.msactiontable_xp24 import (
    Xp24MsActionTable,
)
from xp.models.actiontable.msactiontable_xp33 import Xp33MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
)


class TestActionTableDownloadService:
    """Test cases for ActionTableDownloadService."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

        mock = Mock(spec=ConbusEventProtocol)
        mock.on_connection_made = Mock()
        mock.on_connection_made.connect = Mock()
        mock.on_connection_made.disconnect = Mock()
        mock.on_telegram_sent = Mock()
        mock.on_telegram_sent.connect = Mock()
        mock.on_telegram_received = Mock()
        mock.on_telegram_received.connect = Mock()
        mock.on_telegram_received.disconnect = Mock()
        mock.on_read_datapoint_received = Mock()
        mock.on_read_datapoint_received.connect = Mock()
        mock.on_read_datapoint_received.disconnect = Mock()
        mock.on_actiontable_chunk_received = Mock()
        mock.on_actiontable_chunk_received.connect = Mock()
        mock.on_actiontable_chunk_received.disconnect = Mock()
        mock.on_eof_received = Mock()
        mock.on_eof_received.connect = Mock()
        mock.on_eof_received.disconnect = Mock()
        mock.on_timeout = Mock()
        mock.on_timeout.connect = Mock()
        mock.on_timeout.disconnect = Mock()
        mock.on_failed = Mock()
        mock.on_failed.connect = Mock()
        mock.on_failed.disconnect = Mock()
        return mock

    @pytest.fixture
    def mock_actiontable_serializer(self):
        """Create mock serializer."""
        return Mock()

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
    def service(
        self,
        mock_conbus_protocol,
        mock_actiontable_serializer,
        mock_xp20_serializer,
        mock_xp24_serializer,
        mock_xp33_serializer,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_actiontable_serializer,
            msactiontable_serializer_xp20=mock_xp20_serializer,
            msactiontable_serializer_xp24=mock_xp24_serializer,
            msactiontable_serializer_xp33=mock_xp33_serializer,
        )

    @pytest.fixture
    def sample_xp24_msactiontable(self):
        """Create sample XP24 MsActionTable for testing."""
        return Xp24MsActionTable(
            input1_action=Xp24InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input2_action=Xp24InputAction(
                type=InputActionType.ON, param=TimeParam.T5SEC
            ),
            input3_action=Xp24InputAction(
                type=InputActionType.LEVELSET, param=TimeParam.T5MIN
            ),
            input4_action=Xp24InputAction(
                type=InputActionType.SCENESET, param=TimeParam.T2MIN
            ),
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
        mock_actiontable_serializer,
        mock_xp20_serializer,
        mock_xp24_serializer,
        mock_xp33_serializer,
    ):
        """Test service can be initialized with required dependencies."""
        service = ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_actiontable_serializer,
            msactiontable_serializer_xp20=mock_xp20_serializer,
            msactiontable_serializer_xp24=mock_xp24_serializer,
            msactiontable_serializer_xp33=mock_xp33_serializer,
        )

        assert service.conbus_protocol == mock_conbus_protocol
        assert service.msactiontable_serializer_xp20 == mock_xp20_serializer
        assert service.msactiontable_serializer_xp24 == mock_xp24_serializer
        assert service.msactiontable_serializer_xp33 == mock_xp33_serializer
        assert service.serial_number == ""
        assert service.actiontable_data == []

    def test_configure_xp24(self, service, mock_xp24_serializer):
        """Test configure method with xp24 action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.MSACTIONTABLE_XP24,
            timeout_seconds=10.0,
        )

        assert service.serial_number == "0123450001"
        assert service.serializer == mock_xp24_serializer
        assert service.conbus_protocol.timeout_seconds == 10.0

    def test_configure_xp20(self, service, mock_xp20_serializer):
        """Test configure method with xp20 action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.MSACTIONTABLE_XP20,
        )

        assert service.serializer == mock_xp20_serializer

    def test_configure_xp33(self, service, mock_xp33_serializer):
        """Test configure method with xp33 action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.MSACTIONTABLE_XP33,
        )

        assert service.serializer == mock_xp33_serializer

    def test_configure_actiontable(self, service, mock_actiontable_serializer):
        """Test configure method with standard action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.ACTIONTABLE,
        )

        assert service.serializer == mock_actiontable_serializer

    def test_context_manager(self, service):
        """Test service works as context manager."""
        with service as ctx_service:
            assert ctx_service is service
            # actiontable_data should be reset
            assert service.actiontable_data == []

    def test_context_manager_resets_state(self, service):
        """Test context manager resets state on entry."""
        # Set some state
        service.actiontable_data = ["some", "data"]

        with service:
            # State should be reset
            assert service.actiontable_data == []

    def test_start_reactor_calls_protocol(self, service):
        """Test start_reactor delegates to protocol."""
        service.start_reactor()
        service.conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor_calls_protocol(self, service):
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()
        service.conbus_protocol.stop_reactor.assert_called_once()

    def test_set_timeout(self, service):
        """Test set_timeout configures protocol timeout."""
        service.set_timeout(5.0)
        assert service.conbus_protocol.timeout_seconds == 5.0

    def test_signals_connected_on_init(self, service, mock_conbus_protocol):
        """Test protocol signals are connected on initialization."""
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_idle_state_on_init(self, service):
        """Test service starts in idle state."""
        assert service.idle.is_active

    def test_configure_raises_when_not_idle(self, service):
        """Test configure raises error when not in idle state."""
        # Simulate being in a non-idle state by triggering do_connect
        service.do_connect()

        with pytest.raises(RuntimeError, match="Cannot configure while download"):
            service.configure(
                serial_number="0123450001",
                actiontable_type=ActionTableType.MSACTIONTABLE_XP24,
            )
