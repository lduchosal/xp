"""Integration tests for conbus raw CLI commands.

Tests the complete flow from CLI input to output,
ensuring proper integration between all layers.
"""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus_raw import ConbusRawResponse


class TestConbusRawIntegration:
    """Test class for conbus raw CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("xp.cli.commands.conbus_raw_commands.ConbusRawService")
    def test_conbus_raw_single_telegram(self, mock_service_class):
        """Test conbus raw command with single telegram."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusRawResponse(
            success=True,
            sent_telegrams="<S2113010000F02D12>",
            received_telegrams=["<R2113010000F02D12>"],
        )
        mock_service.send_raw_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "raw", "<S2113010000F02D12>"])

        assert result.exit_code == 0
        assert "<R2113010000F02D12>" in result.output
        mock_service.send_raw_telegrams.assert_called_once_with("<S2113010000F02D12>")

    @patch("xp.cli.commands.conbus_raw_commands.ConbusRawService")
    def test_conbus_raw_multiple_telegrams(self, mock_service_class):
        """Test conbus raw command with multiple telegrams."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusRawResponse(
            success=True,
            sent_telegrams="<S2113010000F02D12><S2113010001F02D12><S2113010002F02D12>",
            received_telegrams=[
                "<R2113010000F02D12>",
                "<R2113010001F02D12>",
                "<S2113010002F02D12>",
            ],
        )
        mock_service.send_raw_telegrams.return_value = mock_response

        raw_input = "<S2113010000F02D12><S2113010001F02D12><S2113010002F02D12>"
        result = self.runner.invoke(cli, ["conbus", "raw", raw_input])

        assert result.exit_code == 0
        output_lines = result.output.strip().split("\n")
        assert "<R2113010000F02D12>" in output_lines
        assert "<R2113010001F02D12>" in output_lines
        assert "<S2113010002F02D12>" in output_lines
        mock_service.send_raw_telegrams.assert_called_once_with(raw_input)

    @patch("xp.cli.commands.conbus_raw_commands.ConbusRawService")
    def test_conbus_raw_connection_error(self, mock_service_class):
        """Test conbus raw command with connection error."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with error
        mock_response = ConbusRawResponse(success=False, error="Connection failed")
        mock_service.send_raw_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "raw", "<S2113010000F02D12>"])

        assert (
            result.exit_code == 0
        )  # CLI doesn't exit with error code, but shows error
        assert "Error: Connection failed" in result.output

    @patch("xp.cli.commands.conbus_raw_commands.ConbusRawService")
    def test_conbus_raw_no_response(self, mock_service_class):
        """Test conbus raw command with no response."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with no received telegrams
        mock_response = ConbusRawResponse(
            success=True, sent_telegrams="<S2113010000F02D12>", received_telegrams=[]
        )
        mock_service.send_raw_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "raw", "<S2113010000F02D12>"])

        assert result.exit_code == 0
        assert "No response received" in result.output

    def test_conbus_raw_help_command(self):
        """Test conbus raw help command."""
        result = self.runner.invoke(cli, ["conbus", "raw", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Send raw telegram sequence to Conbus server" in output
        assert "RAW_TELEGRAMS" in output

    def test_conbus_raw_missing_arguments(self):
        """Test conbus raw command with missing arguments."""
        result = self.runner.invoke(cli, ["conbus", "raw"])

        assert result.exit_code != 0
        assert "Usage: cli conbus raw [OPTIONS] RAW_TELEGRAMS" in result.output

    @patch("xp.cli.commands.conbus_raw_commands.ConbusRawService")
    def test_conbus_raw_service_exception(self, mock_service_class):
        """Test conbus raw command when service raises exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        from xp.services.conbus_raw_service import ConbusRawError

        mock_service.send_raw_telegrams.side_effect = ConbusRawError("Service error")

        result = self.runner.invoke(cli, ["conbus", "raw", "<S2113010000F02D12>"])

        # The CLI should handle the exception gracefully
        assert result.exit_code != 0 or "Service error" in result.output

    def test_conbus_raw_command_registration(self):
        """Test that conbus raw command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "raw" in result.output
