"""Integration tests for XP24 Action Table functionality."""

import json
from unittest.mock import Mock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.actiontable.actiontable_type import ActionTableType
from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
)
from xp.utils.dependencies import ServiceContainer


class TestXp24ActionTableIntegration:
    """Integration tests for XP24 action table CLI operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.valid_serial = "0123450001"
        self.invalid_serial = "1234567890"  # Valid format but will cause service error

    def _create_mock_service(self, action_table=None, error=None):
        """
        Create mock service with signal pattern.

        Args:
            action_table: Optional action table to return on success.
            error: Optional error message to trigger error callback.

        Returns:
            Mock service object configured with signals.
        """
        mock_service = Mock(spec=ActionTableDownloadService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Create mock signals
        mock_service.on_progress = Mock()
        mock_service.on_finish = Mock()
        mock_service.on_actiontable_received = Mock()
        mock_service.on_error = Mock()

        # Track connected callbacks
        progress_callbacks = []
        finish_callbacks = []
        actiontable_received_callbacks = []
        error_callbacks = []

        def connect_progress(callback):
            """
            Connect progress callback.

            Args:
                callback: Callback function to connect.
            """
            progress_callbacks.append(callback)

        def connect_finish(callback):
            """
            Connect finish callback.

            Args:
                callback: Callback function to connect.
            """
            finish_callbacks.append(callback)

        def connect_actiontable_received(callback):
            """
            Connect actiontable_received callback.

            Args:
                callback: Callback function to connect.
            """
            actiontable_received_callbacks.append(callback)

        def connect_error(callback):
            """
            Connect error callback.

            Args:
                callback: Callback function to connect.
            """
            error_callbacks.append(callback)

        mock_service.on_progress.connect = connect_progress
        mock_service.on_finish.connect = connect_finish
        mock_service.on_actiontable_received.connect = connect_actiontable_received
        mock_service.on_error.connect = connect_error

        def mock_start_reactor():
            """Mock start_reactor that triggers callbacks."""
            if error:
                for callback in error_callbacks:
                    callback(error)
            elif action_table:
                short_format = ["XP24 T:0 ON:4 LS:12 SS:11"]
                for callback in actiontable_received_callbacks:
                    callback(action_table, short_format)
                for callback in finish_callbacks:
                    callback()

        mock_service.configure = Mock()
        mock_service.start_reactor.side_effect = mock_start_reactor
        mock_service.stop_reactor = Mock()
        return mock_service

    def test_xp24_download_action_table(self):
        """Test downloading action table from module."""
        # Create mock action table
        mock_action_table = Xp24MsActionTable(
            input1_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input2_action=InputAction(type=InputActionType.ON, param=TimeParam.T5SEC),
            input3_action=InputAction(
                type=InputActionType.LEVELSET, param=TimeParam.T2MIN
            ),
            input4_action=InputAction(
                type=InputActionType.SCENESET, param=TimeParam.T2MIN
            ),
            mutex12=False,
            mutex34=True,
            mutual_deadtime=Xp24MsActionTable.MS300,
            curtain12=False,
            curtain34=True,
        )

        mock_service = self._create_mock_service(action_table=mock_action_table)

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
        mock_service.configure.assert_called_once_with(
            serial_number=self.valid_serial,
            actiontable_type=ActionTableType.MSACTIONTABLE_XP24,
        )

        # Verify JSON output structure
        output = json.loads(result.output)
        assert "serial_number" in output
        assert "xpmoduletype" in output
        assert "msaction_table" in output
        assert "xp24_msaction_table" in output
        assert output["serial_number"] == self.valid_serial
        assert output["xpmoduletype"] == "xp24"

        # Verify short format
        assert output["xp24_msaction_table"] == "XP24 T:0 ON:4 LS:12 SS:11"

        # Verify action table structure
        action_table = output["msaction_table"]
        assert action_table["input1_action"]["type"] == str(InputActionType.TOGGLE)
        assert action_table["input1_action"]["param"] == TimeParam.NONE.value
        assert action_table["input2_action"]["type"] == str(InputActionType.ON)
        assert action_table["input2_action"]["param"] == TimeParam.T5SEC.value
        assert action_table["mutex34"] is True
        assert action_table["curtain34"] is True

    def test_xp24_download_action_table_invalid_serial(self):
        """Test downloading with invalid serial number."""
        mock_service = self._create_mock_service(error="Invalid serial number")

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

        # Verify error in output
        assert "Error: Invalid serial number" in result.output

    def test_xp24_download_action_table_connection_error(self):
        """Test downloading with network failure."""
        mock_service = self._create_mock_service(error="Conbus communication failed")

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

        # Verify error in output
        assert "Error: Conbus communication failed" in result.output
