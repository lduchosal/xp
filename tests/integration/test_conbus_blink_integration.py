"""Integration tests for Conbus blink functionality."""

from unittest.mock import MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_blink import ConbusBlinkResponse
from xp.models.telegram.system_function import SystemFunction


class TestConbusBlinkIntegration:
    """Integration test cases for Conbus blink operations."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_conbus_blink_on(self):
        """Test blink on command."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusBlinkResponse(
            success=True,
            serial_number="0012345008",
            system_function=SystemFunction.BLINK,
            operation="on",
        )

        # Make the mock service call the callback immediately
        def mock_send_blink_telegram(
            serial_number, on_or_off, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                on_or_off: Blink on or off.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            finish_callback(mock_response)

        mock_service.send_blink_telegram.side_effect = mock_send_blink_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "blink", "on", "0012345008"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"operation": "on"' in result.output
        mock_service.send_blink_telegram.assert_called_once()

    def test_conbus_blink_off(self):
        """Test blink off command."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusBlinkResponse(
            success=True,
            serial_number="0012345008",
            system_function=SystemFunction.UNBLINK,
            operation="off",
        )

        # Make the mock service call the callback immediately
        def mock_send_blink_telegram(
            serial_number, on_or_off, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                on_or_off: Blink on or off.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            finish_callback(mock_response)

        mock_service.send_blink_telegram.side_effect = mock_send_blink_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "blink", "off", "0012345008"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"operation": "off"' in result.output
        mock_service.send_blink_telegram.assert_called_once()

    def test_conbus_blink_connection_error(self):
        """Test blink command with connection error."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with error
        mock_response = ConbusBlinkResponse(
            success=False,
            serial_number="0012345008",
            system_function=SystemFunction.BLINK,
            operation="on",
            error="Connection failed",
        )

        # Make the mock service call the callback immediately
        def mock_send_blink_telegram(
            serial_number, on_or_off, finish_callback, timeout_seconds=None
        ):
            """Test helper function.

            Args:
                serial_number: Serial number of the module.
                on_or_off: Blink on or off.
                finish_callback: Callback when finished.
                timeout_seconds: Timeout in seconds.
            """
            finish_callback(mock_response)

        mock_service.send_blink_telegram.side_effect = mock_send_blink_telegram

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "blink", "on", "0012345008"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0  # CLI doesn't exit with error code
        assert '"success": false' in result.output
        assert '"error": "Connection failed"' in result.output

    def test_conbus_blink_help_command(self):
        """Test blink help command."""
        result = self.runner.invoke(cli, ["conbus", "blink", "on", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Send blink command to start blinking module LED" in output
        assert "SERIAL_NUMBER" in output

    def test_conbus_blink_missing_arguments(self):
        """Test blink command with missing arguments."""
        result = self.runner.invoke(cli, ["conbus", "blink", "on"])

        assert result.exit_code != 0
        assert "Usage: cli conbus blink on [OPTIONS] SERIAL_NUMBER" in result.output

    def test_conbus_blink_service_exception(self):
        """Test blink command when service raises exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Make the service raise an exception when send_blink_telegram is called
        mock_service.send_blink_telegram.side_effect = Exception("Service error")

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli,
            ["conbus", "blink", "on", "0012345008"],
            obj={"container": mock_container},
        )

        # The CLI should handle the exception gracefully
        assert result.exit_code != 0

    def test_conbus_blink_command_registration(self):
        """Test that conbus blink command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "blink" in result.output
