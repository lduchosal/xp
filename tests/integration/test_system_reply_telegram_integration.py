"""Integration tests for system and reply telegram CLI commands.

Tests the complete flow from CLI input to output for system and reply telegrams,
ensuring proper integration between all layers.
"""

import json

import pytest
from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.telegram.datapoint_type import DataPointType


class TestSystemTelegramCLI:
    """Test class for system telegram CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_parse_system_telegram_command(self):
        """Test telegram parse command."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F02D18FN>"])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["serial_number"] == "0020012521"
        assert output_data["system_function"]["description"] == "READ_DATAPOINT"
        assert output_data["datapoint_type"]["description"] == "TEMPERATURE"
        assert output_data["checksum"] == "FN"
        assert output_data["telegram_type"] == "S"

    def test_parse_system_telegram_json_output(self):
        """Test telegram parse command with JSON output."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F02D18FN>"])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["serial_number"] == "0020012521"
        assert output_data["system_function"]["code"] == "02"
        assert output_data["system_function"]["description"] == "READ_DATAPOINT"
        assert output_data["datapoint_type"]["code"] == "18"
        assert output_data["datapoint_type"]["description"] == "TEMPERATURE"
        assert output_data["checksum"] == "FN"
        assert output_data["telegram_type"] == "S"
        assert "timestamp" in output_data

    def test_parse_system_telegram_different_functions(self):
        """Test parsing different system function types."""
        # Update firmware
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F01D18FN>"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["system_function"]["description"] == "DISCOVERY"

        # Read config
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F03D18FN>"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["system_function"]["description"] == "READ_CONFIG"

    def test_parse_system_telegram_different_data_points(self):
        """Test parsing different data point types."""
        # Humidity
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F02D19FN>"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["datapoint_type"]["description"] == "SW_TOP_VERSION"

        # Status
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F02D00FN>"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["datapoint_type"]["description"] == "MODULE_TYPE"

    def test_parse_system_telegram_invalid_format(self):
        """Test parsing invalid system telegram format."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<S002001252F02D18FN>"])

        assert result.exit_code == 1

        # Parse JSON error output
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Invalid system telegram format" in output_data["error"]
        assert output_data["raw_input"] == "<S002001252F02D18FN>"

    def test_parse_system_telegram_invalid_format_json(self):
        """Test parsing invalid system telegram format with JSON output."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<S002001252F02D18FN>"])

        assert result.exit_code == 1
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Invalid system telegram format" in output_data["error"]
        assert output_data["raw_input"] == "<S002001252F02D18FN>"

    def test_parse_system_telegram_unknown_function(self):
        """Test parsing system telegram with unknown function."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F99D18FN>"])

        assert result.exit_code == 1
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Unknown system function code: 99" in output_data["error"]


class TestReplyTelegramCLI:
    """Test class for reply telegram CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_parse_reply_telegram_command(self):
        """Test telegram parse command."""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<R0020012521F02D18+26,0§CIL>"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["serial_number"] == "0020012521"
        assert output_data["system_function"]["description"] == "READ_DATAPOINT"
        assert output_data["datapoint_type"]["description"] == "TEMPERATURE"
        assert output_data["data_value"]["parsed"]["value"] == 26.0
        assert output_data["data_value"]["parsed"]["unit"] == "°C"
        assert output_data["checksum"] == "IL"
        assert output_data["telegram_type"] == "R"

    def test_parse_reply_telegram_json_output(self):
        """Test telegram parse command with JSON output."""
        result = self.runner.invoke(
            cli,
            [
                "telegram",
                "parse",
                "<R0020012521F02D18+26,0§CIL>",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["serial_number"] == "0020012521"
        assert output_data["system_function"]["code"] == "02"
        assert output_data["system_function"]["description"] == "READ_DATAPOINT"
        assert output_data["datapoint_type"]["code"] == DataPointType.TEMPERATURE.value
        assert output_data["datapoint_type"]["description"] == "TEMPERATURE"
        assert output_data["data_value"]["raw"] == "+26,0§C"
        assert output_data["data_value"]["parsed"]["parsed"] is True
        assert output_data["data_value"]["parsed"]["value"] == 26.0
        assert output_data["data_value"]["parsed"]["unit"] == "°C"
        assert output_data["checksum"] == "IL"
        assert output_data["telegram_type"] == "R"

    def test_parse_reply_telegram_different_data_types(self):
        """Test parsing different reply data types."""
        # Humidity
        result = self.runner.invoke(
            cli,
            [
                "telegram",
                "parse",
                "<R0020012521F02D19+65,5§RHIL>",
            ],
        )
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["data_value"]["parsed"]["value"] == 65.5
        assert output_data["data_value"]["parsed"]["unit"] == "%RH"

        # VOLTAGE
        result = self.runner.invoke(
            cli,
            [
                "telegram",
                "parse",
                "<R0020012521F02D20+12,5§VIL>",
            ],
        )

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["data_value"]["parsed"]["value"] == 12.5
        assert output_data["data_value"]["parsed"]["unit"] == "V"

    def test_parse_reply_telegram_status_data(self):
        """Test parsing reply telegram with status data."""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<R0020012521F02D00OKIL>"]
        )

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["data_value"]["parsed"]["raw_value"] == "OK"
        assert output_data["data_value"]["parsed"]["parsed"] is True

    def test_parse_reply_telegram_negative_temperature(self):
        """Test parsing reply telegram with negative temperature."""
        result = self.runner.invoke(
            cli,
            [
                "telegram",
                "parse",
                "<R0020012521F02D18-15,2§CIL>",
            ],
        )

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["data_value"]["parsed"]["value"] == -15.2
        assert output_data["data_value"]["parsed"]["formatted"] == "-15.2°C"

    def test_parse_reply_telegram_invalid_format(self):
        """Test parsing invalid reply telegram format."""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<R002001252F02D18+26,0§CIL>"]
        )

        assert result.exit_code == 1

        # Parse JSON error output
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Invalid reply telegram format" in output_data["error"]
        assert output_data["raw_input"] == "<R002001252F02D18+26,0§CIL>"

    def test_parse_reply_telegram_invalid_format_json(self):
        """Test parsing invalid reply telegram format with JSON output."""
        result = self.runner.invoke(
            cli,
            ["telegram", "parse", "<R002001252F02D18+26,0§CIL>"],
        )

        assert result.exit_code == 1
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Invalid reply telegram format" in output_data["error"]


class TestAutoDetectTelegramCLI:
    """Test class for auto-detect telegram CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_parse_telegram_event(self):
        """Test parse command with event telegram."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        # Should use event telegram formatting
        assert "module_type" in output_data
        assert "event_type" in output_data
        assert output_data["module_type"] == 14
        assert output_data["module_info"]["name"] == "XP2606"

    def test_parse_telegram_system(self):
        """Test parse command with system telegram."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F02D18FN>"])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        # Should use system telegram formatting
        assert output_data["telegram_type"] == "S"
        assert output_data["system_function"]["description"] == "READ_DATAPOINT"
        assert output_data["datapoint_type"]["description"] == "TEMPERATURE"

    def test_parse_telegram_reply(self):
        """Test parse command with reply telegram."""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<R0020012521F02D18+26,0§CIL>"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        # Should use reply telegram formatting
        assert output_data["telegram_type"] == "R"
        assert output_data["data_value"]["parsed"]["value"] == 26.0
        assert output_data["data_value"]["parsed"]["unit"] == "°C"

    def test_parse_telegram_json_output(self):
        """Test parse command with JSON output for different types."""
        # Event telegram
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert "module_type" in output_data
        assert "event_type" in output_data

        # System telegram
        result = self.runner.invoke(cli, ["telegram", "parse", "<S0020012521F02D18FN>"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["telegram_type"] == "S"
        assert "serial_number" in output_data

        # Reply telegram
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<R0020012521F02D18+26,0§CIL>"]
        )

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["telegram_type"] == "R"
        assert "data_value" in output_data

    def test_parse_telegram_unknown_type(self):
        """Test parse command with unknown telegram type."""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<X0020012521F02D18+26,0§CIL>"]
        )

        assert result.exit_code == 1

        # Parse JSON error output
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Unknown telegram type" in output_data["error"]
        assert output_data["raw_input"] == "<X0020012521F02D18+26,0§CIL>"

    def test_parse_telegram_unknown_type_json(self):
        """Test parse command with unknown telegram type and JSON output."""
        result = self.runner.invoke(
            cli, ["telegram", "parse", "<X0020012521F02D18+26,0§CIL>"]
        )

        assert result.exit_code == 1
        output_data = json.loads(result.output)
        assert output_data["success"] is False
        assert "Unknown telegram type" in output_data["error"]

    def test_parse_telegram_help(self):
        """Test parse command help."""
        result = self.runner.invoke(cli, ["telegram", "parse", "--help"])

        assert result.exit_code == 0
        assert "Auto-detect and parse any type of telegram" in result.output
        assert "" in result.output

    @pytest.mark.parametrize(
        "telegram,expected_type",
        [
            ("<E14L00I02MAK>", "E"),
            ("<S0020012521F02D18FN>", "S"),
            ("<R0020012521F02D18+26,0§CIL>", "R"),
        ],
    )
    def test_parse_telegram_type_detection(self, telegram, expected_type):
        """Test that parse correctly detects and processes different telegram types."""
        result = self.runner.invoke(cli, ["telegram", "parse", telegram])

        assert result.exit_code == 0
        output_data = json.loads(result.output)

        if expected_type == "E":
            # Event telegrams don't have telegram_type field but have unique fields
            assert "module_type" in output_data
            assert "event_type" in output_data
        else:
            assert output_data.get("telegram_type") == expected_type


class TestTelegramCLIIntegration:
    """Test integration between all telegram CLI commands."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_telegram_help_shows_all_commands(self):
        """Test that telegram help shows all available commands."""
        result = self.runner.invoke(cli, ["telegram", "--help"])

        assert result.exit_code == 0
        output = result.output

        # Check that all telegram commands are listed
        assert "parse" in output
        assert "validate" in output

    def test_all_telegram_commands_exist(self):
        """Test that all telegram commands can be invoked."""
        # Test each command with help to ensure they exist
        commands = [
            "parse",
            "validate",
        ]

        for cmd in commands:
            result = self.runner.invoke(cli, ["telegram", cmd, "--help"])
            assert result.exit_code == 0, f"Command 'telegram {cmd}' failed"

    def test_consistent_json_output_format(self):
        """Test that all telegram commands have consistent JSON output format."""
        # All commands should include timestamp and proper structure
        telegrams = [
            ("parse", "<E14L00I02MAK>"),
            ("parse", "<S0020012521F02D18FN>"),
            ("parse", "<R0020012521F02D18+26,0§CIL>"),
            ("parse", "<E14L00I02MAK>"),
        ]

        for cmd, telegram in telegrams:
            result = self.runner.invoke(cli, ["telegram", cmd, telegram])

            assert result.exit_code == 0
            output_data = json.loads(result.output)

            # All should have timestamp
            assert "timestamp" in output_data
            # All should have proper structure (no error field when successful)
            if cmd != "validate":  # validate has different structure
                assert "timestamp" in output_data

    def test_error_handling_consistency(self):
        """Test that all telegram commands handle errors consistently."""
        # Test with invalid telegrams
        invalid_telegrams = [
            ("parse", "<INVALID>"),
            ("parse", "<INVALID>"),
            ("parse", "<INVALID>"),
            ("parse", "<INVALID>"),
        ]

        for cmd, telegram in invalid_telegrams:
            result = self.runner.invoke(cli, ["telegram", cmd, telegram])

            assert result.exit_code == 1
            output_data = json.loads(result.output)

            # All should have consistent error structure
            assert "success" in output_data
            assert output_data["success"] is False
            assert "error" in output_data
            assert "raw_input" in output_data
            assert output_data["raw_input"] == telegram

    def test_missing_arguments_handled_consistently(self):
        """Test that missing arguments are handled consistently."""
        commands = ["parse", "parse", "parse", "parse"]

        for cmd in commands:
            result = self.runner.invoke(cli, ["telegram", cmd])

            assert result.exit_code != 0  # Should fail with missing arguments
            assert "Missing argument" in result.output or "Usage:" in result.output
