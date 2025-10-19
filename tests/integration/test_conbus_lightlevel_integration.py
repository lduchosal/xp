"""Integration tests for Conbus lightlevel functionality."""

from datetime import datetime
from unittest.mock import MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_lightlevel import ConbusLightlevelResponse


class TestConbusLightlevelIntegration:
    """Integration test cases for Conbus lightlevel operations."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_conbus_lightlevel_set(self):
        """Test setting specific light level."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusLightlevelResponse(
            success=True,
            serial_number="0012345008",
            output_number=2,
            level=50,
            timestamp=datetime.now(),
        )

        # Make the mock service call the callback immediately
        def mock_set_lightlevel(
            serial_number, output_number, level, finish_callback, timeout_seconds=None
        ):
            finish_callback(mock_response)

        mock_service.set_lightlevel.side_effect = mock_set_lightlevel

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "lightlevel", "set", "0012345008", "2", "50"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"level": 50' in result.output
        mock_service.set_lightlevel.assert_called_once()

    def test_conbus_lightlevel_off(self):
        """Test turning light off."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusLightlevelResponse(
            success=True,
            serial_number="0012345008",
            output_number=2,
            level=0,
            timestamp=datetime.now(),
        )

        # Make the mock service call the callback immediately
        def mock_turn_off(
            serial_number, output_number, finish_callback, timeout_seconds=None
        ):
            finish_callback(mock_response)

        mock_service.turn_off.side_effect = mock_turn_off

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "lightlevel", "off", "0012345008", "2"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"level": 0' in result.output
        mock_service.turn_off.assert_called_once()

    def test_conbus_lightlevel_on(self):
        """Test turning light on."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusLightlevelResponse(
            success=True,
            serial_number="0012345008",
            output_number=2,
            level=80,
            timestamp=datetime.now(),
        )

        # Make the mock service call the callback immediately
        def mock_turn_on(
            serial_number, output_number, finish_callback, timeout_seconds=None
        ):
            finish_callback(mock_response)

        mock_service.turn_on.side_effect = mock_turn_on

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "lightlevel", "on", "0012345008", "2"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"level": 80' in result.output
        mock_service.turn_on.assert_called_once()

    def test_conbus_lightlevel_connection_error(self):
        """Test lightlevel command with connection error."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with error
        mock_response = ConbusLightlevelResponse(
            success=False,
            serial_number="0012345008",
            output_number=2,
            level=None,
            timestamp=datetime.now(),
            error="Connection failed",
        )

        # Make the mock service call the callback immediately
        def mock_set_lightlevel(
            serial_number, output_number, level, finish_callback, timeout_seconds=None
        ):
            finish_callback(mock_response)

        mock_service.set_lightlevel.side_effect = mock_set_lightlevel

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "lightlevel", "set", "0012345008", "2", "50"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0  # CLI doesn't exit with error code
        assert '"success": false' in result.output
        assert '"error": "Connection failed"' in result.output

    def test_conbus_lightlevel_invalid_level(self):
        """Test invalid level values are caught by CLI validation."""
        result = self.runner.invoke(
            cli,
            ["conbus", "lightlevel", "set", "0012345008", "2", "150"],
        )

        # Should be caught by CLI validation before reaching service
        assert result.exit_code == 2  # CLI validation error
        assert "Invalid value for 'LEVEL'" in result.output
        assert "150 is not in the range 0<=x<=100" in result.output

    def test_conbus_lightlevel_service_exception(self):
        """Test lightlevel command when service raises exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Make the service raise an exception
        mock_service.set_lightlevel.side_effect = Exception("Service error")

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "lightlevel", "set", "0012345008", "2", "50"],
            obj={"container": mock_container},
        )

        # The CLI should handle the exception gracefully
        assert result.exit_code != 0

    def test_conbus_lightlevel_help_command(self):
        """Test lightlevel help command."""
        result = self.runner.invoke(cli, ["conbus", "lightlevel", "--help"])

        assert result.exit_code == 0
        assert "set" in result.output
        assert "on" in result.output
        assert "off" in result.output

    def test_conbus_lightlevel_command_registration(self):
        """Test that conbus lightlevel command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "lightlevel" in result.output
