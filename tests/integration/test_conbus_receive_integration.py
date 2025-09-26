"""Integration tests for conbus receive CLI commands.

Tests the complete flow from CLI input to output,
ensuring proper integration between all layers.
"""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus_receive import ConbusReceiveResponse


class TestConbusReceiveIntegration:
    """Test class for conbus receive CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("xp.cli.commands.conbus_receive_commands.ConbusReceiveService")
    def test_conbus_receive_single_telegram(self, mock_service_class):
        """Test conbus receive command with single telegram response."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusReceiveResponse(
            success=True, received_telegrams=["<R2113010000F02D12>"]
        )
        mock_service.receive_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "receive"])

        assert result.exit_code == 0
        assert "<R2113010000F02D12>" in result.output
        mock_service.receive_telegrams.assert_called_once()

    @patch("xp.cli.commands.conbus_receive_commands.ConbusReceiveService")
    def test_conbus_receive_multiple_telegrams(self, mock_service_class):
        """Test conbus receive command with multiple telegram responses."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response
        mock_response = ConbusReceiveResponse(
            success=True,
            received_telegrams=[
                "<R2113010000F02D12>",
                "<R2113010001F02D12>",
                "<S2113010002F02D12>",
                "<E12L1BAK>",
            ],
        )
        mock_service.receive_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "receive"])

        assert result.exit_code == 0
        output_lines = result.output.strip().split("\n")
        assert "<R2113010000F02D12>" in output_lines
        assert "<R2113010001F02D12>" in output_lines
        assert "<S2113010002F02D12>" in output_lines
        assert "<E12L1BAK>" in output_lines
        mock_service.receive_telegrams.assert_called_once()

    @patch("xp.cli.commands.conbus_receive_commands.ConbusReceiveService")
    def test_conbus_receive_connection_error(self, mock_service_class):
        """Test conbus receive command with connection error."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with error
        mock_response = ConbusReceiveResponse(
            success=False, error="Failed to connect to server: Connection timeout"
        )
        mock_service.receive_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "receive"])

        assert (
            result.exit_code == 0
        )  # CLI doesn't exit with error code, but shows error
        assert "Error: Failed to connect to server: Connection timeout" in result.output

    @patch("xp.cli.commands.conbus_receive_commands.ConbusReceiveService")
    def test_conbus_receive_no_telegrams(self, mock_service_class):
        """Test conbus receive command with no waiting telegrams."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with no received telegrams
        mock_response = ConbusReceiveResponse(success=True, received_telegrams=[])
        mock_service.receive_telegrams.return_value = mock_response

        result = self.runner.invoke(cli, ["conbus", "receive"])

        assert result.exit_code == 0
        # Should have no output when no telegrams received (silent success)
        assert result.output.strip() == ""

    def test_conbus_receive_help_command(self):
        """Test conbus receive help command."""
        result = self.runner.invoke(cli, ["conbus", "receive", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Receive waiting event telegrams from Conbus server" in output
        assert "xp conbus receive" in output

    @patch("xp.cli.commands.conbus_receive_commands.ConbusReceiveService")
    def test_conbus_receive_service_exception(self, mock_service_class):
        """Test conbus receive command when service raises exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        from xp.services.conbus_receive_service import ConbusReceiveError

        mock_service.receive_telegrams.side_effect = ConbusReceiveError("Service error")

        result = self.runner.invoke(cli, ["conbus", "receive"])

        # The CLI should handle the exception gracefully
        assert result.exit_code != 0 or "Service error" in result.output

    def test_conbus_receive_command_registration(self):
        """Test that conbus receive command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "receive" in result.output
