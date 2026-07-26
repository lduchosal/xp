# Copyright (c) 2025 ldvchosal
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
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

# Timeout values used to exercise timeout configuration.
CONFIGURE_TIMEOUT_SECONDS = 10.0
SET_TIMEOUT_SECONDS = 5.0


class TestActionTableDownloadService:
    """Test cases for ActionTableDownloadService."""

    @pytest.fixture
    def mock_conbus_protocol(self) -> Mock:
        """Create mock ConbusEventProtocol.

        Returns:
            Mock ConbusEventProtocol.

        """
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
    def mock_actiontable_serializer(self) -> Mock:
        """Create mock serializer.

        Returns:
            Mock serializer.

        """
        return Mock()

    @pytest.fixture
    def mock_xp20_serializer(self) -> Mock:
        """Create mock XP20 serializer.

        Returns:
            Mock XP20 serializer.

        """
        return Mock()

    @pytest.fixture
    def mock_xp24_serializer(self) -> Mock:
        """Create mock XP24 serializer.

        Returns:
            Mock XP24 serializer.

        """
        return Mock()

    @pytest.fixture
    def mock_xp33_serializer(self) -> Mock:
        """Create mock XP33 serializer.

        Returns:
            Mock XP33 serializer.

        """
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol: Mock,
        mock_actiontable_serializer: Mock,
        mock_xp20_serializer: Mock,
        mock_xp24_serializer: Mock,
        mock_xp33_serializer: Mock,
    ) -> ActionTableDownloadService:
        """Create service instance for testing.

        Returns:
            Service instance for testing.

        """
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_actiontable_serializer,
            msactiontable_serializer_xp20=mock_xp20_serializer,
            msactiontable_serializer_xp24=mock_xp24_serializer,
            msactiontable_serializer_xp33=mock_xp33_serializer,
        )

    @pytest.fixture
    def sample_xp24_msactiontable(self) -> Xp24MsActionTable:
        """Create sample XP24 MsActionTable for testing.

        Returns:
            Sample XP24 MsActionTable for testing.

        """
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
    def sample_xp20_msactiontable(self) -> Xp20MsActionTable:
        """Create sample XP20 MsActionTable for testing.

        Returns:
            Sample XP20 MsActionTable for testing.

        """
        return Xp20MsActionTable()

    @pytest.fixture
    def sample_xp33_msactiontable(self) -> Xp33MsActionTable:
        """Create sample XP33 MsActionTable for testing.

        Returns:
            Sample XP33 MsActionTable for testing.

        """
        return Xp33MsActionTable()

    def test_service_initialization(
        self,
        mock_conbus_protocol: Mock,
        mock_actiontable_serializer: Mock,
        mock_xp20_serializer: Mock,
        mock_xp24_serializer: Mock,
        mock_xp33_serializer: Mock,
    ) -> None:
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
        assert not service.serial_number
        assert service.actiontable_data == []

    def test_configure_xp24(
        self, service: ActionTableDownloadService, mock_xp24_serializer: Mock
    ) -> None:
        """Test configure method with xp24 action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.MSACTIONTABLE_XP24,
            timeout_seconds=CONFIGURE_TIMEOUT_SECONDS,
        )

        assert service.serial_number == "0123450001"
        assert service.serializer == mock_xp24_serializer
        assert service.conbus_protocol.timeout_seconds == CONFIGURE_TIMEOUT_SECONDS

    def test_configure_xp20(
        self, service: ActionTableDownloadService, mock_xp20_serializer: Mock
    ) -> None:
        """Test configure method with xp20 action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.MSACTIONTABLE_XP20,
        )

        assert service.serializer == mock_xp20_serializer

    def test_configure_xp33(
        self, service: ActionTableDownloadService, mock_xp33_serializer: Mock
    ) -> None:
        """Test configure method with xp33 action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.MSACTIONTABLE_XP33,
        )

        assert service.serializer == mock_xp33_serializer

    def test_configure_actiontable(
        self, service: ActionTableDownloadService, mock_actiontable_serializer: Mock
    ) -> None:
        """Test configure method with standard action table type."""
        service.configure(
            serial_number="0123450001",
            actiontable_type=ActionTableType.ACTIONTABLE,
        )

        assert service.serializer == mock_actiontable_serializer

    def test_context_manager(self, service: ActionTableDownloadService) -> None:
        """Test service works as context manager."""
        with service as ctx_service:
            assert ctx_service is service
            # actiontable_data should be reset
            assert service.actiontable_data == []

    def test_context_manager_resets_state(
        self, service: ActionTableDownloadService
    ) -> None:
        """Test context manager resets state on entry."""
        # Set some state
        service.actiontable_data = ["some", "data"]

        with service:
            # State should be reset
            assert service.actiontable_data == []

    def test_start_reactor_calls_protocol(
        self, service: ActionTableDownloadService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to protocol."""
        service.start_reactor()
        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor_calls_protocol(
        self, service: ActionTableDownloadService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_set_timeout(self, service: ActionTableDownloadService) -> None:
        """Test set_timeout configures protocol timeout."""
        service.set_timeout(SET_TIMEOUT_SECONDS)
        assert service.conbus_protocol.timeout_seconds == SET_TIMEOUT_SECONDS

    @pytest.mark.usefixtures("service")
    def test_signals_connected_on_init(self, mock_conbus_protocol: Mock) -> None:
        """Test protocol signals are connected on initialization."""
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_idle_state_on_init(self, service: ActionTableDownloadService) -> None:
        """Test service starts in idle state."""
        assert service.idle.is_active

    def test_configure_raises_when_not_idle(
        self, service: ActionTableDownloadService
    ) -> None:
        """Test configure raises error when not in idle state."""
        # Simulate being in a non-idle state by triggering do_connect
        service.do_connect()

        with pytest.raises(RuntimeError, match="Cannot configure while download"):
            service.configure(
                serial_number="0123450001",
                actiontable_type=ActionTableType.MSACTIONTABLE_XP24,
            )
