"""Unit tests for conbus actiontable CLI commands."""

from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from xp.cli.commands.conbus.conbus_actiontable_commands import (
    conbus_download_actiontable,
)
from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


class TestConbusActionTableCommands:
    """Test cases for conbus actiontable CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

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
                command=InputActionType.TURNOFF,
                parameter=TimeParam.NONE,
            )
        ]
        return ActionTable(entries=entries)

    def _create_mock_service(self, actiontable=None, error=None):
        """Create mock service with callback pattern.

        Args:
            actiontable: Optional ActionTable to return on success.
            error: Optional error message to trigger error callback.

        Returns:
            Mock service object configured with callbacks.
        """
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)

        def mock_start(
            serial_number, progress_callback, finish_callback, error_callback
        ):
            """Execute mock start operation.

            Args:
                serial_number: Serial number for the operation.
                progress_callback: Callback for progress updates.
                finish_callback: Callback for successful completion.
                error_callback: Callback for error conditions.
            """
            if error:
                error_callback(error)
            else:
                if actiontable:
                    finish_callback(actiontable)

        mock_service.start.side_effect = mock_start
        return mock_service

    def test_conbus_download_actiontable_success(self, runner, sample_actiontable):
        """Test successful actiontable download command."""
        # Setup mock service
        mock_service = self._create_mock_service(actiontable=sample_actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0
        mock_service.start.assert_called_once()

        # Verify output contains expected data
        assert "0000012345" in result.output
        assert "actiontable" in result.output

    def test_conbus_download_actiontable_output_format(
        self, runner, sample_actiontable
    ):
        """Test actiontable download command output format."""
        # Setup mock service
        mock_service = self._create_mock_service(actiontable=sample_actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0

        # The output should contain JSON with the actiontable data
        # It may be on multiple lines due to indentation
        assert "0000012345" in result.output
        assert "actiontable" in result.output
        assert "entries" in result.output

    def test_conbus_download_actiontable_error_handling(self, runner):
        """Test actiontable download command error handling."""
        # Setup mock service to call error_callback
        mock_service = self._create_mock_service(error="Communication failed")

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify error handling
        assert "Communication failed" in result.output

    def test_conbus_download_actiontable_invalid_serial(self, runner):
        """Test actiontable download command with invalid serial number."""
        # Execute command with invalid serial
        result = runner.invoke(conbus_download_actiontable, ["invalid"])

        # Should fail due to serial number validation
        assert result.exit_code != 0

    def test_conbus_download_actiontable_context_manager(
        self, runner, sample_actiontable
    ):
        """Test that service is properly used as context manager."""
        # Setup mock service
        mock_service = self._create_mock_service(actiontable=sample_actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify context manager usage
        assert result.exit_code == 0
        mock_service.__enter__.assert_called_once()
        mock_service.__exit__.assert_called_once()

    def test_conbus_download_actiontable_help(self, runner):
        """Test actiontable download command help."""
        result = runner.invoke(conbus_download_actiontable, ["--help"])

        assert result.exit_code == 0
        assert "Download action table from XP module" in result.output
        assert "SERIAL_NUMBER" in result.output

    def test_conbus_download_actiontable_json_serialization(self, runner):
        """Test that complex objects are properly serialized to JSON."""
        # Create actiontable with enum values
        entry = ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=5,
            module_input=2,
            module_output=3,
            inverted=True,
            command=InputActionType.TURNON,
            parameter=TimeParam.T2SEC,
        )
        actiontable = ActionTable(entries=[entry])

        # Setup mock service
        mock_service = self._create_mock_service(actiontable=actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success and output contains expected data
        assert result.exit_code == 0

        # The output should contain the actiontable data
        # It may be on multiple lines due to indentation and include progress dots
        assert "0000012345" in result.output
        assert "actiontable" in result.output
        assert "entries" in result.output

    def test_download_actiontable_includes_short_format(
        self, runner, sample_actiontable
    ):
        """Test that actiontable download includes actiontable_short field."""
        # Setup mock service
        mock_service = self._create_mock_service(actiontable=sample_actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0

        # Verify actiontable_short field exists
        assert "actiontable_short" in result.output

    def test_download_actiontable_short_format_correct(
        self, runner, sample_actiontable
    ):
        """Test that actiontable_short field contains correctly formatted entries."""
        # Setup mock service
        mock_service = self._create_mock_service(actiontable=sample_actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0

        # Verify short format is present with semicolons
        assert "CP20 0 0 > 1 TURNOFF;" in result.output

    def test_download_actiontable_backward_compatible(self, runner, sample_actiontable):
        """Test that JSON actiontable field is still present for backward compatibility."""
        # Setup mock service
        mock_service = self._create_mock_service(actiontable=sample_actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0

        # Verify both formats are present
        assert "actiontable_short" in result.output
        assert "actiontable" in result.output
        assert "entries" in result.output

    def test_download_actiontable_short_with_parameter(self, runner):
        """Test actiontable_short displays parameter when non-zero."""
        # Create actiontable with parameter
        entry = ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=0,
            module_input=2,
            module_output=1,
            inverted=False,
            command=InputActionType.TURNON,
            parameter=TimeParam.T1SEC,  # value = 2
        )
        actiontable = ActionTable(entries=[entry])

        # Setup mock service
        mock_service = self._create_mock_service(actiontable=actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0

        # Verify parameter is included in output
        assert "CP20 0 2 > 1 TURNON 2;" in result.output

    def test_download_actiontable_short_inverted(self, runner):
        """Test actiontable_short displays inverted commands with ~ prefix."""
        # Create actiontable with inverted command
        entry = ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=0,
            module_input=1,
            module_output=1,
            inverted=True,
            command=InputActionType.TURNON,
            parameter=TimeParam.NONE,
        )
        actiontable = ActionTable(entries=[entry])

        # Setup mock service
        mock_service = self._create_mock_service(actiontable=actiontable)

        # Setup mock container to resolve ActionTableService
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container

        # Execute command
        result = runner.invoke(
            conbus_download_actiontable,
            ["012345"],
            obj={"container": mock_service_container},
        )

        # Verify success
        assert result.exit_code == 0

        # Verify inverted prefix is present
        assert "~TURNON" in result.output
        assert "CP20 0 1 > 1 ~TURNON;" in result.output
