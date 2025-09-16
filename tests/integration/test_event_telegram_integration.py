import pytest
from click.testing import CliRunner
import json
from src.xp.cli.main import cli


class TestEventTelegramIntegration:
    """Integration tests for telegram command functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.runner = CliRunner()

    def test_parse_event_telegram_command_success(self):
        """Test successful telegram parsing via CLI"""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0
        assert (
            "XP2606 (Type 14) Link 00 Input 02 (push_button) pressed" in result.output
        )
        assert "Raw: <E14L00I02MAK>" in result.output
        assert "Checksum: AK" in result.output

    def test_parse_event_telegram_command_json_output(self):
        """Test telegram parsing with JSON output"""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<E14L00I02MAK>", "--json-output"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == 14
        assert output["link_number"] == 0
        assert output["input_number"] == 2
        assert output["event_type"] == "M"
        assert output["event_type_name"] == "button_press"
        assert output["input_type"] == "push_button"
        assert output["checksum"] == "AK"
        assert output["raw_telegram"] == "<E14L00I02MAK>"

    def test_parse_event_telegram_command_with_checksum_validation(self):
        """Test telegram parsing with checksum validation"""
        result = self.runner.invoke(
            cli, ["telegram", "parse-event", "<E14L00I02MAK>", "--validate-checksum"]
        )

        assert result.exit_code == 0
        assert "Checksum validation:" in result.output

    def test_parse_event_telegram_command_invalid_format(self):
        """Test telegram parsing with invalid format"""
        result = self.runner.invoke(cli, ["telegram", "parse", "INVALID"])

        assert result.exit_code == 1
        assert "Error parsing telegram" in result.output

    def test_parse_event_telegram_command_invalid_format_json(self):
        """Test telegram parsing with invalid format and JSON output"""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "INVALID", "--json-output"]
        )

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output
        assert output["raw_input"] == "INVALID"

    def test_parse_multiple_event_telegrams_command_success(self):
        """Test parsing multiple telegrams via CLI"""
        data = "Some data <E14L00I02MAK> more <E14L01I03BB1> end"
        result = self.runner.invoke(cli, ["telegram", "parse-multiple", data])

        assert result.exit_code == 0
        assert "Found 2 telegrams:" in result.output
        assert (
            "XP2606 (Type 14) Link 00 Input 02 (push_button) pressed" in result.output
        )
        assert (
            "XP2606 (Type 14) Link 01 Input 03 (push_button) released" in result.output
        )

    def test_parse_multiple_event_telegrams_command_json_output(self):
        """Test parsing multiple telegrams with JSON output"""
        data = "Some data <E14L00I02MAK> more <E14L01I03BB1> end"
        result = self.runner.invoke(
            cli, ["telegram", "parse-multiple", data, "--json-output"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["success"] is True
        assert output["count"] == 2
        assert len(output["telegrams"]) == 2

        # Check first telegram
        first_telegram = output["telegrams"][0]
        assert first_telegram["module_type"] == 14
        assert first_telegram["event_type_name"] == "button_press"

        # Check second telegram
        second_telegram = output["telegrams"][1]
        assert second_telegram["module_type"] == 14
        assert second_telegram["event_type_name"] == "button_release"

    def test_parse_multiple_event_telegrams_command_no_telegrams(self):
        """Test parsing multiple telegrams when none exist"""
        result = self.runner.invoke(
            cli, ["telegram", "parse-multiple", "No telegrams here"]
        )

        assert result.exit_code == 0
        assert "Found 0 telegrams:" in result.output

    def test_validate_telegram_command_valid(self):
        """Test telegram validation with valid telegram"""
        result = self.runner.invoke(cli, ["telegram", "validate", "<E14L00I02MAK>"])

        assert result.exit_code == 0
        assert "✓ Telegram format is valid" in result.output
        assert "Checksum:" in result.output
        assert (
            "XP2606 (Type 14) Link 00 Input 02 (push_button) pressed" in result.output
        )

    def test_validate_telegram_command_valid_json(self):
        """Test telegram validation with valid telegram and JSON output"""
        result = self.runner.invoke(
            cli, ["telegram", "validate", "<E14L00I02MAK>", "--json-output"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["success"] is True
        assert output["valid_format"] is True
        assert output["valid_checksum"] is True
        assert "telegram" in output

    def test_validate_telegram_command_invalid(self):
        """Test telegram validation with invalid telegram"""
        result = self.runner.invoke(cli, ["telegram", "validate", "INVALID"])

        assert result.exit_code == 1
        assert "\u2717 Input format is invalid" in result.output
        assert "Error:" in result.output

    def test_validate_telegram_command_invalid_json(self):
        """Test telegram validation with invalid telegram and JSON output"""
        result = self.runner.invoke(
            cli, ["telegram", "validate", "INVALID", "--json-output"]
        )

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["valid_format"] is False
        assert "error" in output
        assert output["raw_input"] == "INVALID"

    def test_telegram_help_command(self):
        """Test telegram help command"""
        result = self.runner.invoke(cli, ["telegram", "--help"])

        assert result.exit_code == 0
        assert "Event telegram operations" in result.output
        assert "parse" in result.output
        assert "parse-multiple" in result.output
        assert "validate" in result.output

    def test_main_cli_help(self):
        """Test main CLI help"""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "XP CLI tool for remote console bus operations" in result.output
        assert "telegram" in result.output

    def test_parse_event_telegram_button_release(self):
        """Test parsing button release telegram"""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L01I03BB1>"])

        assert result.exit_code == 0
        assert (
            "XP2606 (Type 14) Link 01 Input 03 (push_button) released" in result.output
        )

    def test_parse_event_telegram_ir_remote(self):
        """Test parsing IR remote telegram"""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I25MXX>"])

        assert result.exit_code == 0
        assert "XP2606 (Type 14) Link 00 Input 25 (ir_remote) pressed" in result.output

    def test_parse_event_telegram_proximity_sensor(self):
        """Test parsing proximity sensor telegram"""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I90MXX>"])

        assert result.exit_code == 0
        assert (
            "XP2606 (Type 14) Link 00 Input 90 (proximity_sensor) pressed"
            in result.output
        )

    def test_end_to_end_workflow(self):
        """Test complete workflow from parsing to validation"""
        telegram = "<E14L00I02MAK>"

        # Parse telegram
        parse_result = self.runner.invoke(
            cli, ["telegram", "parse", telegram, "--json-output"]
        )
        assert parse_result.exit_code == 0
        parse_data = json.loads(parse_result.output)

        # Validate telegram
        validate_result = self.runner.invoke(
            cli, ["telegram", "validate", telegram, "--json-output"]
        )
        assert validate_result.exit_code == 0
        validate_data = json.loads(validate_result.output)

        # Ensure consistency
        assert parse_data["module_type"] == validate_data["telegram"]["module_type"]
        assert parse_data["event_type"] == validate_data["telegram"]["event_type"]

    def test_parse_event_telegram_json_with_checksum_validation(self):
        """Test JSON output with checksum validation (cover line 43)"""
        result = self.runner.invoke(
            cli,
            [
                "telegram",
                "parse-event",
                "<E14L00I02MAK>",
                "--json-output",
                "--validate-checksum",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output and verify checksum_valid field is present
        output = json.loads(result.output)
        assert "checksum_valid" in output
        assert isinstance(output["checksum_valid"], bool)

    def test_parse_multiple_event_telegrams_exception_handling(self):
        """Test exception handling in parse-multiple command"""
        # Create a scenario that might cause an exception after parsing starts
        # For example, by patching the service method to raise an exception
        import unittest.mock

        with unittest.mock.patch(
            "src.xp.services.telegram_service.TelegramService.parse_multiple_telegrams"
        ) as mock_method:
            mock_method.side_effect = ValueError("Test exception")

            result = self.runner.invoke(
                cli, ["telegram", "parse-multiple", "test data"]
            )
            assert result.exit_code == 1
            assert "Error parsing telegram" in result.output

    def test_parse_multiple_event_telegrams_exception_handling_json(self):
        """Test exception handling in parse-multiple command with JSON output"""
        import unittest.mock

        with unittest.mock.patch(
            "src.xp.services.telegram_service.TelegramService.parse_multiple_telegrams"
        ) as mock_method:
            mock_method.side_effect = ValueError("Test exception")

            result = self.runner.invoke(
                cli, ["telegram", "parse-multiple", "test data", "--json-output"]
            )
            assert result.exit_code == 1

            # Should be valid JSON
            output = json.loads(result.output)
            assert output["success"] is False
            assert "error" in output
