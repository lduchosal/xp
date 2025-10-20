"""Integration tests for event telegram command functionality."""

import json

from click.testing import CliRunner

from xp.cli.main import cli


class TestEventTelegramIntegration:
    """Integration tests for telegram command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_parse_event_telegram_command_success(self):
        """Test that successful telegram parsing via CLI works."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == 14
        assert output["link_number"] == 0
        assert output["output_number"] == 2
        assert output["event_type"] == "M"
        assert output["event_type_name"] == "button_press"
        assert output["input_type"] == "push_button"
        assert output["checksum"] == "AK"
        assert output["raw_telegram"] == "<E14L00I02MAK>"

    def test_parse_event_telegram_command_json_output(self):
        """Test telegram parsing with JSON output."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == 14
        assert output["link_number"] == 0
        assert output["output_number"] == 2
        assert output["event_type"] == "M"
        assert output["event_type_name"] == "button_press"
        assert output["input_type"] == "push_button"
        assert output["checksum"] == "AK"
        assert output["raw_telegram"] == "<E14L00I02MAK>"

    def test_parse_event_telegram_command_invalid_format(self):
        """Test telegram parsing with invalid format."""
        result = self.runner.invoke(cli, ["telegram", "parse", "INVALID"])

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output

    def test_parse_event_telegram_command_invalid_format_json(self):
        """Test telegram parsing with invalid format and JSON output."""
        result = self.runner.invoke(cli, ["telegram", "parse", "INVALID"])

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output

    def test_validate_telegram_command_valid_json(self):
        """Test telegram validation with valid telegram and JSON output."""
        result = self.runner.invoke(cli, ["telegram", "validate", "<E14L00I02MAK>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["success"] is True
        assert output["valid_format"] is True
        assert output["valid_checksum"] is True
        assert "telegram" in output

    def test_validate_telegram_command_invalid(self):
        """Test telegram validation with invalid telegram."""
        result = self.runner.invoke(cli, ["telegram", "validate", "INVALID"])

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output
        assert output["raw_input"] == "INVALID"

    def test_validate_telegram_command_invalid_json(self):
        """Test telegram validation with invalid telegram and JSON output."""
        result = self.runner.invoke(cli, ["telegram", "validate", "INVALID"])

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output
        assert output["raw_input"] == "INVALID"

    def test_telegram_help_command(self):
        """Test telegram help command."""
        result = self.runner.invoke(cli, ["telegram", "--help"])

        assert result.exit_code == 0
        assert "event telegram operations" in result.output
        assert "parse" in result.output
        assert "validate" in result.output

    def test_main_cli_help(self):
        """Test main CLI help."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "XP CLI tool for remote console bus operations" in result.output
        assert "telegram" in result.output

    def test_parse_event_telegram_button_release(self):
        """Test parsing button release telegram."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L01I03BB1>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == 14
        assert output["link_number"] == 1
        assert output["output_number"] == 3
        assert output["event_type_name"] == "button_release"

    def test_parse_event_telegram_ir_remote(self):
        """Test parsing IR remote telegram."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I25MXX>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == 14
        assert output["link_number"] == 0
        assert output["output_number"] == 25
        assert output["input_type"] == "ir_remote"

    def test_parse_event_telegram_proximity_sensor(self):
        """Test parsing proximity sensor telegram."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I90MXX>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == 14
        assert output["link_number"] == 0
        assert output["output_number"] == 90
        assert output["input_type"] == "proximity_sensor"

    def test_end_to_end_workflow(self):
        """Test complete workflow from parsing to validation."""
        telegram = "<E14L00I02MAK>"

        # Parse telegram
        parse_result = self.runner.invoke(cli, ["telegram", "parse", telegram])
        assert parse_result.exit_code == 0
        parse_data = json.loads(parse_result.output)

        # Validate telegram
        validate_result = self.runner.invoke(cli, ["telegram", "validate", telegram])
        assert validate_result.exit_code == 0
        validate_data = json.loads(validate_result.output)

        # Ensure consistency
        assert parse_data["module_type"] == validate_data["telegram"]["module_type"]
        assert parse_data["event_type"] == validate_data["telegram"]["event_type"]
