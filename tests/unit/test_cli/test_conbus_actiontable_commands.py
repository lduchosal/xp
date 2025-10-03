"""Unit tests for conbus actiontable CLI commands."""

import json
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
from xp.services.conbus.actiontable.actiontable_service import ActionTableError


class TestConbusActionTableCommands:
    """Test cases for conbus actiontable CLI commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    @pytest.fixture
    def sample_actiontable(self):
        """Create sample ActionTable for testing"""
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

    def test_conbus_download_actiontable_success(self, runner, sample_actiontable):
        """Test successful actiontable download command"""
        # Setup mock service
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)
        mock_service.download_actiontable.return_value = sample_actiontable

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
        mock_service.download_actiontable.assert_called_once_with("0000012345")

        # Verify output format
        output_data = json.loads(result.output)
        assert "serial_number" in output_data
        assert "actiontable" in output_data
        assert output_data["serial_number"] == "0000012345"
        assert "entries" in output_data["actiontable"]

    def test_conbus_download_actiontable_output_format(
        self, runner, sample_actiontable
    ):
        """Test actiontable download command output format"""
        # Setup mock service
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)
        mock_service.download_actiontable.return_value = sample_actiontable

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

        # Parse and verify JSON output
        output_data = json.loads(result.output)

        # Check structure
        expected_keys = {"serial_number", "actiontable"}
        assert set(output_data.keys()) == expected_keys

        # Check actiontable structure
        actiontable_data = output_data["actiontable"]
        assert "entries" in actiontable_data
        assert isinstance(actiontable_data["entries"], list)

        # Check first entry structure
        if actiontable_data["entries"]:
            entry = actiontable_data["entries"][0]
            expected_entry_keys = {
                "module_type",
                "link_number",
                "module_input",
                "module_output",
                "inverted",
                "command",
                "parameter",
            }
            assert set(entry.keys()) == expected_entry_keys

    def test_conbus_download_actiontable_error_handling(self, runner):
        """Test actiontable download command error handling"""
        # Setup mock service to raise error
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)
        mock_service.download_actiontable.side_effect = ActionTableError(
            "Communication failed"
        )

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
        assert result.exit_code != 0
        assert "Communication failed" in result.output

    def test_conbus_download_actiontable_invalid_serial(self, runner):
        """Test actiontable download command with invalid serial number"""
        # Execute command with invalid serial
        result = runner.invoke(conbus_download_actiontable, ["invalid"])

        # Should fail due to serial number validation
        assert result.exit_code != 0

    def test_conbus_download_actiontable_context_manager(
        self, runner, sample_actiontable
    ):
        """Test that service is properly used as context manager"""
        # Setup mock service
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)
        mock_service.download_actiontable.return_value = sample_actiontable

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
        """Test actiontable download command help"""
        result = runner.invoke(conbus_download_actiontable, ["--help"])

        assert result.exit_code == 0
        assert "Download action table from XP module" in result.output
        assert "SERIAL_NUMBER" in result.output

    def test_conbus_download_actiontable_json_serialization(self, runner):
        """Test that complex objects are properly serialized to JSON"""
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
        mock_service = Mock()
        mock_service.__enter__ = Mock(return_value=mock_service)
        mock_service.__exit__ = Mock(return_value=None)
        mock_service.download_actiontable.return_value = actiontable

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

        # Verify JSON can be parsed and contains expected data
        assert result.exit_code == 0
        output_data = json.loads(result.output)

        entry_data = output_data["actiontable"]["entries"][0]
        assert entry_data["link_number"] == 5
        assert entry_data["module_input"] == 2
        assert entry_data["module_output"] == 3
