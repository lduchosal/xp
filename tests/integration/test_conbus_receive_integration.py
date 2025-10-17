"""Integration tests for conbus receive CLI commands.

Tests the complete flow from CLI input to output,
ensuring proper integration between all layers.
"""

from unittest.mock import MagicMock

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.conbus.conbus_receive import ConbusReceiveResponse


class TestConbusReceiveIntegration:
    """Test class for conbus receive CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_conbus_receive_no_telegrams(self):
        """Test conbus receive command with no waiting telegrams."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.__enter__.return_value = mock_service
        mock_service.__exit__.return_value = None

        # Mock the response with no received telegrams
        mock_response = ConbusReceiveResponse(success=True, received_telegrams=[])
        mock_service.receive_telegrams.return_value = mock_response

        # Mock the container
        mock_container = MagicMock()
        mock_container.get_container().resolve.return_value = mock_service

        result = self.runner.invoke(
            cli, ["conbus", "receive"], obj={"container": mock_container}
        )

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

    def test_conbus_receive_command_registration(self):
        """Test that conbus receive command is properly registered."""
        result = self.runner.invoke(cli, ["conbus", "--help"])

        assert result.exit_code == 0
        assert "receive" in result.output
