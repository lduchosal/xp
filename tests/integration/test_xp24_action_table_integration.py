"""Integration tests for XP24 Action Table functionality."""

import json
from unittest.mock import Mock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.msactiontable_service import (
    MsActionTableService,
)
from xp.utils.dependencies import ServiceContainer


class TestXp24ActionTableIntegration:
    """Integration tests for XP24 action table CLI operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "1234567890"  # Valid format but will cause service error

    def test_xp24_download_action_table(self):
        """Test downloading action table from module."""
        # Create mock service
        mock_service = Mock(spec=MsActionTableService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Create mock action table
        mock_action_table = Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TOGGLE, TimeParam.NONE),
            input2_action=InputAction(InputActionType.ON, TimeParam.T5SEC),
            input3_action=InputAction(InputActionType.LEVELSET, TimeParam.T2MIN),
            input4_action=InputAction(InputActionType.SCENESET, TimeParam.T2MIN),
            mutex12=False,
            mutex34=True,
            mutual_deadtime=Xp24MsActionTable.MS300,
            curtain12=False,
            curtain34=True,
        )

        # Mock the start method to call finish_callback immediately
        def mock_start(
            serial_number,
            xpmoduletype,
            progress_callback,
            finish_callback,
            error_callback,
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                xpmoduletype: XP module type.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                error_callback: Callback for errors.
            """
            finish_callback(mock_action_table)

        mock_service.start.side_effect = mock_start

        # Create mock container
        mock_container = Mock(spec=ServiceContainer)
        mock_punq_container = Mock()
        mock_punq_container.resolve.return_value = mock_service
        mock_container.get_container.return_value = mock_punq_container

        # Run CLI command with mock container in context
        result = self.runner.invoke(
            cli,
            ["conbus", "msactiontable", "download", self.valid_serial, "xp24"],
            obj={"container": mock_container},
        )

        # Verify success
        assert result.exit_code == 0
        mock_service.start.assert_called_once()

        # Verify JSON output structure
        output = json.loads(result.output)
        assert "serial_number" in output
        assert "xpmoduletype" in output
        assert "action_table" in output
        assert output["serial_number"] == self.valid_serial
        assert output["xpmoduletype"] == "xp24"

        # Verify action table structure
        action_table = output["action_table"]
        assert action_table["input1_action"]["type"] == str(InputActionType.TOGGLE)
        assert action_table["input1_action"]["param"] == TimeParam.NONE.value
        assert action_table["input2_action"]["type"] == str(InputActionType.ON)
        assert action_table["input2_action"]["param"] == TimeParam.T5SEC.value
        assert action_table["mutex34"] is True
        assert action_table["curtain34"] is True

    def test_xp24_download_action_table_invalid_serial(self):
        """Test downloading with invalid serial number."""
        # Create mock service with error
        mock_service = Mock(spec=MsActionTableService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Mock the start method to call error_callback
        def mock_start(
            serial_number,
            xpmoduletype,
            progress_callback,
            finish_callback,
            error_callback,
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                xpmoduletype: XP module type.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                error_callback: Callback for errors.
            """
            error_callback("Invalid serial number")

        mock_service.start.side_effect = mock_start

        # Create mock container
        mock_container = Mock(spec=ServiceContainer)
        mock_punq_container = Mock()
        mock_punq_container.resolve.return_value = mock_service
        mock_container.get_container.return_value = mock_punq_container

        # Run CLI command
        result = self.runner.invoke(
            cli,
            ["conbus", "msactiontable", "download", self.invalid_serial, "xp24"],
            obj={"container": mock_container},
        )

        # Verify error
        assert result.exit_code != 0
        assert "Error: Invalid serial number" in result.output

    def test_xp24_download_action_table_connection_error(self):
        """Test downloading with network failure."""
        # Create mock service with error
        mock_service = Mock(spec=MsActionTableService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Mock the start method to call error_callback
        def mock_start(
            serial_number,
            xpmoduletype,
            progress_callback,
            finish_callback,
            error_callback,
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                xpmoduletype: XP module type.
                progress_callback: Callback for progress updates.
                finish_callback: Callback when finished.
                error_callback: Callback for errors.
            """
            error_callback("Conbus communication failed")

        mock_service.start.side_effect = mock_start

        # Create mock container
        mock_container = Mock(spec=ServiceContainer)
        mock_punq_container = Mock()
        mock_punq_container.resolve.return_value = mock_service
        mock_container.get_container.return_value = mock_punq_container

        # Run CLI command
        result = self.runner.invoke(
            cli,
            ["conbus", "msactiontable", "download", self.valid_serial, "xp24"],
            obj={"container": mock_container},
        )

        # Verify error
        assert result.exit_code != 0
        assert "Error: Conbus communication failed" in result.output
