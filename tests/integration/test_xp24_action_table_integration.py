"""Integration tests for XP24 Action Table functionality."""

import json
from unittest.mock import Mock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.msactiontable.msactiontable_download_service import (
    MsActionTableDownloadService,
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
        mock_service = Mock(spec=MsActionTableDownloadService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

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

        # Store the callbacks that are connected
        callbacks = {"on_finish": None, "on_error": None}

        def mock_on_finish_connect(callback):
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_finish"] = callback

        def mock_on_error_connect(callback):
            """Mock on_error event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_error"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_error.connect.side_effect = mock_on_error_connect

        # Mock the start method to call finish_callback immediately
        def mock_start(serial_number, xpmoduletype):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                xpmoduletype: XP module type.
            """
            # Call the on_finish callback that was connected
            if callbacks["on_finish"]:
                callbacks["on_finish"](mock_action_table, "XP24 T:0 ON:4 LS:12 SS:11")

        def mock_start_reactor():
            """Mock reactor start method."""
            # Do nothing in test
            pass

        def mock_stop_reactor():
            """Mock reactor stop method."""
            # Do nothing in test
            pass

        mock_service.start.side_effect = mock_start
        mock_service.start_reactor.side_effect = mock_start_reactor
        mock_service.stop_reactor.side_effect = mock_stop_reactor

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
        assert "msaction_table" in output
        assert "msaction_table_short" in output
        assert output["serial_number"] == self.valid_serial
        assert output["xpmoduletype"] == "xp24"

        # Verify short format
        assert output["msaction_table_short"] == "XP24 T:0 ON:4 LS:12 SS:11"

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
        # Create mock service with error
        mock_service = Mock(spec=MsActionTableDownloadService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Store the callbacks that are connected
        callbacks = {"on_finish": None, "on_error": None}

        def mock_on_finish_connect(callback):
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_finish"] = callback

        def mock_on_error_connect(callback):
            """Mock on_error event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_error"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_error.connect.side_effect = mock_on_error_connect

        # Mock the start method to call error_callback
        def mock_start(serial_number, xpmoduletype):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                xpmoduletype: XP module type.
            """
            # Call the on_error callback that was connected
            if callbacks["on_error"]:
                callbacks["on_error"]("Invalid serial number")
            # Call on_finish with None to signal failure
            if callbacks["on_finish"]:
                callbacks["on_finish"](None, "")

        def mock_start_reactor():
            """Mock reactor start method."""
            # Do nothing in test
            pass

        def mock_stop_reactor():
            """Mock reactor stop method."""
            # Do nothing in test
            pass

        mock_service.start.side_effect = mock_start
        mock_service.start_reactor.side_effect = mock_start_reactor
        mock_service.stop_reactor.side_effect = mock_stop_reactor

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
        mock_service = Mock(spec=MsActionTableDownloadService)
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        # Store the callbacks that are connected
        callbacks = {"on_finish": None, "on_error": None}

        def mock_on_finish_connect(callback):
            """Mock on_finish event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_finish"] = callback

        def mock_on_error_connect(callback):
            """Mock on_error event connection.

            Args:
                callback: Callback function to store.
            """
            callbacks["on_error"] = callback

        mock_service.on_finish.connect.side_effect = mock_on_finish_connect
        mock_service.on_error.connect.side_effect = mock_on_error_connect

        # Mock the start method to call error_callback
        def mock_start(serial_number, xpmoduletype):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                xpmoduletype: XP module type.
            """
            # Call the on_error callback that was connected
            if callbacks["on_error"]:
                callbacks["on_error"]("Conbus communication failed")
            # Call on_finish with None to signal failure
            if callbacks["on_finish"]:
                callbacks["on_finish"](None)

        def mock_start_reactor():
            """Mock reactor start method."""
            # Do nothing in test
            pass

        def mock_stop_reactor():
            """Mock reactor stop method."""
            # Do nothing in test
            pass

        mock_service.start.side_effect = mock_start
        mock_service.start_reactor.side_effect = mock_start_reactor
        mock_service.stop_reactor.side_effect = mock_stop_reactor

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
