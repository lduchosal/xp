"""Tests for conbus blink commands."""

from click.testing import CliRunner

from xp.cli.commands.conbus import conbus


class TestConbusBlinkCommands:
    """Test cases for conbus blink and unblink commands."""

    def test_conbus_blink_help(self):
        """Test help text for conbus blink command."""
        result = CliRunner().invoke(conbus, ["blink", "--help"])

        assert result.exit_code == 0
        assert "sending blink telegrams" in result.output
        assert "Usage:" in result.output
        assert "conbus blink [OPTIONS] COMMAND" in result.output

    def test_conbus_unblink_help(self):
        """Test help text for conbus unblink command."""
        result = CliRunner().invoke(conbus, ["blink", "--help"])

        assert result.exit_code == 0
        assert "Usage: conbus blink [OPTIONS] COMMAND [ARGS]" in result.output
        assert "Usage:" in result.output

    def test_conbus_blink_invalid_serial_json(self):
        """Test blink command with invalid serial number and JSON output."""
        result = CliRunner().invoke(conbus, ["blink", "on", "invalid"])

        assert result.exit_code == 2
        assert (
            "Error: Invalid value for 'SERIAL_NUMBER': 'invalid' contains non-numeric characters"
            in result.output
        )
