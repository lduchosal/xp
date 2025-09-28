"""Integration tests for XP24 Action Table functionality."""

import json
from unittest.mock import Mock, patch
from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.input_action_type import InputActionType
from xp.models.xp24_msactiontable import InputAction, Xp24MsActionTable
from xp.services.xp24_action_table_service import (
    Xp24ActionTableError,
)


class TestXp24ActionTableIntegration:
    """Integration tests for XP24 action table CLI operations."""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "1234567890"  # Valid format but will cause service error

    @patch("xp.cli.commands.conbus_msactiontable_commands.Xp24ActionTableService")
    def test_xp24_download_action_table(self, mock_service_class):
        """Test downloading action table from module"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Create mock action table
        mock_action_table = Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TOGGLE, None),
            input2_action=InputAction(InputActionType.TURNON, "5"),
            input3_action=InputAction(InputActionType.LEVELSET, "75"),
            input4_action=InputAction(InputActionType.SCENESET, "3"),
            mutex12=False,
            mutex34=True,
            ms=Xp24MsActionTable.MS300,
            curtain12=False,
            curtain34=True,
        )

        mock_service.download_action_table.return_value = mock_action_table

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.valid_serial]
        )

        # Verify success
        assert result.exit_code == 0
        mock_service.download_action_table.assert_called_once_with(self.valid_serial)

        # Verify JSON output structure
        output = json.loads(result.output)
        assert "serial_number" in output
        assert "action_table" in output
        assert "raw" in output
        assert output["serial_number"] == self.valid_serial

        # Verify action table structure
        action_table = output["action_table"]
        assert action_table["input1_action"]["type"] == "TOGGLE"
        assert action_table["input1_action"]["param"] is None
        assert action_table["input2_action"]["type"] == "TURNON"
        assert action_table["input2_action"]["param"] == "5"
        assert action_table["mutex34"] is True
        assert action_table["curtain34"] is True

    @patch("xp.cli.commands.conbus_msactiontable_commands.Xp24ActionTableService")
    def test_xp24_download_action_table_raw_mode(self, mock_service_class):
        """Test downloading action table in raw mode"""

        # Mock successful response
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_action_table = Xp24MsActionTable()
        mock_service.download_action_table.return_value = mock_action_table

        # Run CLI command with --raw flag
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.valid_serial, "--raw"]
        )

        # Verify success
        assert result.exit_code == 0

        # Verify raw output structure (no action_table field)
        output = json.loads(result.output)
        assert "serial_number" in output
        assert "raw" in output
        assert "action_table" not in output

    @patch("xp.cli.commands.conbus_msactiontable_commands.Xp24ActionTableService")
    def test_xp24_download_action_table_invalid_serial(self, mock_service_class):
        """Test downloading with invalid serial number"""

        # Mock service error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.download_action_table.side_effect = Xp24ActionTableError(
            "Invalid serial number"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.invalid_serial]
        )

        # Verify error
        assert result.exit_code != 0
        assert "Invalid serial number" in result.output

    @patch("xp.cli.commands.conbus_msactiontable_commands.Xp24ActionTableService")
    def test_xp24_download_action_table_connection_error(self, mock_service_class):
        """Test downloading with network failure"""

        # Mock service error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        mock_service.download_action_table.side_effect = Xp24ActionTableError(
            "Conbus communication failed"
        )

        # Run CLI command
        result = self.runner.invoke(
            cli, ["conbus", "msactiontable", "download", self.valid_serial]
        )

        # Verify error
        assert result.exit_code != 0
        assert "Conbus communication failed" in result.output
