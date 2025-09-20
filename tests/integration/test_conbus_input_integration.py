"""Integration tests for system and reply telegram CLI commands.

Tests the complete flow from CLI input to output for system and reply telegrams,
ensuring proper integration between all layers.
"""

import json

from click.testing import CliRunner

from xp.cli.main import cli


class TestConbusInputIntegration:
    """Test class for system telegram CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_conbus_input_on_serial_1(self):
        """Test telegram parse command."""
        result = self.runner.invoke(
            cli, ["conbus", "input", "on", "0020012521", "1"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["success"] == False
