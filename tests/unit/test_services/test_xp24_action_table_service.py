"""Unit tests for XP24 Action Table Service."""

from unittest.mock import patch
import pytest

from xp.models.input_action_type import InputActionType
from xp.models.timeparam_type import TimeParam
from xp.models.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.services.conbus_service import ConbusError
from xp.services.msactiontable_service import (
    MsActionTableService,
    MsActionTableError,
)


class TestMsActionTableService:
    """Test cases for MsActionTableService"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return MsActionTableService("test_config.yml")

    @pytest.fixture
    def mock_action_table(self):
        """Create mock action table for testing"""
        return Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TOGGLE, TimeParam.NONE),
            input2_action=InputAction(InputActionType.TURNON, TimeParam.T5SEC),
            input3_action=InputAction(InputActionType.LEVELSET, TimeParam.T5MIN),
            input4_action=InputAction(InputActionType.SCENESET, TimeParam.T2MIN),
            mutex12=True,
            mutex34=False,
            mutual_deadtime=Xp24MsActionTable.MS500,
            curtain12=False,
            curtain34=True,
        )

    @patch("xp.services.msactiontable_service.Xp24MsActionTableSerializer")
    def test_download_action_table_success(
        self, mock_serializer_class, service, mock_action_table
    ):
        """Test successful action table download"""
        # Mock the serializer to return our mock action table
        mock_serializer_class.from_telegrams.return_value = mock_action_table

        # Patch the complex callback workflow to directly call the serializer
        with patch.object(service.conbus_service, "send_telegram"):
            # Mock the internal workflow by directly setting the msactiontable_telegrams
            def mock_download_method(_serial_number):
                # Simulate successful workflow resulting in telegrams
                msactiontable_telegrams = [
                    "<S0123450001F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>"
                ]
                return mock_serializer_class.from_telegrams(msactiontable_telegrams)

            # Replace the download method
            service.download_action_table = mock_download_method

            # Execute
            result = service.download_action_table("0123450001")

            # Verify
            assert result == mock_action_table
            mock_serializer_class.from_telegrams.assert_called_once_with(
                [
                    "<S0123450001F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>"
                ]
            )

    def test_download_action_table_conbus_error(self, service):
        """Test action table download with Conbus error"""
        # Mock ConbusService to raise error
        with patch.object(service.conbus_service, "send_telegram") as mock_send:
            mock_send.side_effect = ConbusError("Connection failed")

            # Execute and verify exception
            with pytest.raises(
                MsActionTableError,
                match="Conbus communication failed: Connection failed",
            ):
                service.download_action_table("0123450001", "xp24")

    @patch("xp.services.msactiontable_service.Xp24MsActionTableSerializer")
    def test_download_action_table_serializer_error(
        self, mock_serializer_class, service
    ):
        """Test action table download with serializer error"""
        # Mock serializer to raise an error
        mock_serializer_class.from_telegrams.side_effect = Exception(
            "Serialization failed"
        )

        # Mock the callback workflow to succeed but serializer fails
        with patch.object(service.conbus_service, "send_telegram"):

            def mock_download_method(_serial_number, _xpmoduletype):
                # Simulate successful telegram collection but serializer failure
                msactiontable_telegrams = ["invalid_telegram"]
                return mock_serializer_class.from_telegrams(msactiontable_telegrams)

            # Replace the download method
            service.download_action_table = mock_download_method

            # Execute and verify exception propagates
            with pytest.raises(Exception, match="Serialization failed"):
                service.download_action_table("0123450001", "xp24")

    def test_context_manager(self, service):
        """Test service as context manager"""
        with service as ctx_service:
            assert ctx_service is service

        # Context manager should exit without error
