"""Integration tests for checksum CLI commands.

Tests the complete flow from CLI input to output,
ensuring proper integration between all layers.
"""

import json
import pytest
from click.testing import CliRunner
from xp.cli.main import cli


class TestChecksumIntegration:
    """Test class for checksum CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_checksum_calculate_json_output(self):
        """Test checksum calculate command with JSON output."""
        result = self.runner.invoke(cli, ["telegram", "checksum", "calculate", "test"])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["success"] is True
        assert output_data["data"]["input"] == "test"
        assert output_data["data"]["algorithm"] == "simple_xor"
        assert "checksum" in output_data["data"]
        assert "timestamp" in output_data

    def test_checksum_validate_valid_checksum(self):
        """Test checksum validate command with valid checksum."""
        # First calculate a checksum
        calc_result = self.runner.invoke(
            cli, ["telegram", "checksum", "calculate", "test"]
        )
        assert calc_result.exit_code == 0

        calc_data = json.loads(calc_result.output)
        checksum = calc_data["data"]["checksum"]

        # Then validate it
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "validate", "test", checksum]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["success"] is True
        assert output_data["data"]["input"] == "test"

    def test_checksum_validate_invalid_checksum(self):
        """Test checksum validate command with invalid checksum."""
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "validate", "test", "XX"]
        )

        assert result.exit_code == 0
        output = result.output

        assert '"input": "test"' in output
        assert '"expected_checksum": "XX"' in output
        assert '"is_valid": false' in output

    def test_checksum_validate_crc32_algorithm(self):
        """Test checksum validate command with CRC32 algorithm."""
        # First calculate a CRC32 checksum
        calc_result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "test", "--algorithm", "crc32"],
        )
        assert calc_result.exit_code == 0

        calc_data = json.loads(calc_result.output)
        checksum = calc_data["data"]["checksum"]

        # Then validate it
        result = self.runner.invoke(
            cli,
            [
                "telegram",
                "checksum",
                "validate",
                "test",
                checksum,
                "--algorithm",
                "crc32",
            ],
        )

        assert result.exit_code == 0
        output = result.output

        assert '"is_valid": true' in output

    def test_checksum_validate_json_output(self):
        """Test checksum validate command with JSON output."""
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "validate", "test", "XX"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["success"] is True
        assert output_data["data"]["input"] == "test"
        assert output_data["data"]["expected_checksum"] == "XX"
        assert output_data["data"]["is_valid"] is False

    def test_checksum_help_command(self):
        """Test checksum help command."""
        result = self.runner.invoke(cli, ["telegram", "checksum", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Checksum calculation and validation operations" in output
        assert "calculate" in output
        assert "validate" in output

    def test_checksum_calculate_help(self):
        """Test checksum calculate help command."""
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "calculate", "--help"]
        )

        assert result.exit_code == 0
        output = result.output

        assert "Calculate checksum for given data string" in output
        assert "--algorithm" in output

    def test_checksum_validate_help(self):
        """Test checksum validate help command."""
        result = self.runner.invoke(cli, ["telegram", "checksum", "validate", "--help"])

        assert result.exit_code == 0
        output = result.output

        assert "Validate data against expected checksum" in output
        assert "--algorithm" in output

    def test_checksum_calculate_empty_string(self):
        """Test checksum calculate with empty string."""
        result = self.runner.invoke(cli, ["telegram", "checksum", "calculate"])

        assert result.exit_code == 2
        output = result.output

        assert "Usage: cli telegram checksum calculate [OPTIONS] DATA" in output

    def test_checksum_validate_empty_string(self):
        """Test checksum validate with empty string."""
        result = self.runner.invoke(cli, ["telegram", "checksum", "validate", "", "AA"])

        assert result.exit_code == 0
        output = result.output

        assert '"is_valid": true' in output

    def test_algorithm_parameter_validation(self):
        """Test that algorithm parameter accepts only valid values."""
        # Test invalid algorithm
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "calculate", "test", "--algorithm", "invalid"]
        )

        assert result.exit_code != 0
        assert "Invalid value for '--algorithm'" in result.output

    def test_missing_arguments(self):
        """Test commands with missing required arguments."""
        # Missing data argument for calculate
        result = self.runner.invoke(cli, ["telegram", "checksum", "calculate"])
        assert result.exit_code != 0

        # Missing expected_checksum argument for validate
        result = self.runner.invoke(cli, ["telegram", "checksum", "validate", "test"])
        assert result.exit_code != 0

    @pytest.mark.parametrize(
        "test_data",
        [
            "A",
            "ABC",
            "E14L00I02M",
            "Hello World",
            "123456789",
        ],
    )
    def test_checksum_calculate_various_data(self, test_data):
        """Test checksum calculate with various data inputs."""
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "calculate", test_data]
        )

        assert result.exit_code == 0
        assert f'"input": "{test_data}"' in result.output
        assert '"checksum":' in result.output

    @pytest.mark.parametrize("algorithm", ["simple", "crc32"])
    def test_checksum_roundtrip(self, algorithm):
        """Test calculate then validate roundtrip for both algorithms."""
        # Calculate checksum
        calc_result = self.runner.invoke(
            cli,
            [
                "telegram",
                "checksum",
                "calculate",
                "test",
                "--algorithm",
                algorithm,
            ],
        )
        assert calc_result.exit_code == 0

        calc_data = json.loads(calc_result.output)
        checksum = calc_data["data"]["checksum"]

        # Validate the calculated checksum
        validate_result = self.runner.invoke(
            cli,
            [
                "telegram",
                "checksum",
                "validate",
                "test",
                checksum,
                "--algorithm",
                algorithm,
            ],
        )
        assert validate_result.exit_code == 0

        validate_data = json.loads(validate_result.output)
        assert validate_data["data"]["is_valid"] is True

    def test_integration_with_telegram_parse(self):
        """Test integration concept - checksum could be used with telegram parsing."""
        # This tests that the checksum commands are available alongside other commands

        # First test that checksum commands exist
        result = self.runner.invoke(cli, ["telegram", "--help"])
        assert result.exit_code == 0
        assert "checksum" in result.output

        # Test that other command groups still exist
        assert "telegram" in result.output
        assert "module" in result.output

    def test_consistent_output_format(self):
        """Test that output format is consistent with other CLI commands."""
        result = self.runner.invoke(cli, ["telegram", "checksum", "calculate", "test"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)

        # Should follow the same response format as other commands
        assert "success" in output_data
        assert "data" in output_data
        assert "timestamp" in output_data

    def test_error_handling_json_format(self):
        """Test that errors are properly formatted in JSON mode."""
        # This would require creating a scenario that causes an error
        # For now, we test that the JSON structure is maintained
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "validate", "test", "invalid"]
        )

        assert result.exit_code == 0  # Validation failure is not a CLI error
        output_data = json.loads(result.output)

        assert "success" in output_data
        assert output_data["data"]["is_valid"] is False
