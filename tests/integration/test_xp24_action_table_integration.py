"""Integration tests for XP24 Action Table functionality."""

import json
from unittest.mock import Mock, patch
from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.input_action_type import InputActionType
from xp.models.timeparam_type import TimeParam
from xp.models.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.services.msactiontable_service import (
    MsActionTableError,
)


class TestXp24ActionTableIntegration:
    """Integration tests for XP24 action table CLI operations."""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "1234567890"  # Valid format but will cause service error

    @patch("xp.cli.commands.conbus_msactiontable_commands.MsActionTableService")
    def test_xp24_download_action_table(self, mock_service_class):
        """Test downloading action table from module"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Create mock action table
        mock_action_table = Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TOGGLE, TimeParam.NONE),
            input2_action=InputAction(InputActionType.TURNON, TimeParam.T5SEC),
            input3_action=InputAction(InputActionType.LEVELSET, TimeParam.T2MIN),
            input4_action=InputAction(InputActionType.SCENESET, TimeParam.T2MIN),
            mutex12=False,
            mutex34=True,
            mutual_deadtime=Xp24MsActionTable.MS300,
            curtain12=False,
            curtain34=True,
        )

        mock_service.download_action_table.return_value = mock_action_table

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.valid_serial, "xp24"]
        )

        # Verify success
        assert result.exit_code == 0
        mock_service.download_action_table.assert_called_once_with(
            self.valid_serial, "xp24"
        )

        # Verify JSON output structure
        output = json.loads(result.output)
        assert "serial_number" in output
        assert "xpmoduletype" in output
        assert "action_table" in output
        assert output["serial_number"] == self.valid_serial
        assert output["xpmoduletype"] == "xp24"

        # Verify action table structure
        action_table = output["action_table"]
        assert action_table["input1_action"]["type"] == InputActionType.TOGGLE.value
        assert action_table["input1_action"]["param"] == TimeParam.NONE.value
        assert action_table["input2_action"]["type"] == InputActionType.TURNON.value
        assert action_table["input2_action"]["param"] == TimeParam.T5SEC.value
        assert action_table["mutex34"] is True
        assert action_table["curtain34"] is True

    @patch("xp.cli.commands.conbus_msactiontable_commands.MsActionTableService")
    def test_xp24_download_action_table_invalid_serial(self, mock_service_class):
        """Test downloading with invalid serial number"""

        # Mock service error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.download_action_table.side_effect = MsActionTableError(
            "Invalid serial number"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.invalid_serial, "xp24"]
        )

        # Verify error
        assert result.exit_code != 0
        assert "Invalid serial number" in result.output

    @patch("xp.cli.commands.conbus_msactiontable_commands.MsActionTableService")
    def test_xp24_download_action_table_connection_error(self, mock_service_class):
        """Test downloading with network failure"""

        # Mock service error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.download_action_table.side_effect = MsActionTableError(
            "Conbus communication failed"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.valid_serial, "xp24"]
        )

        # Verify error
        assert result.exit_code != 0
        assert "Conbus communication failed" in result.output
