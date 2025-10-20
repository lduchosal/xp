"""Integration tests for checksum CLI commands.

Tests the complete flow from CLI input to output,
ensuring proper integration between all layers.
"""

import json
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from xp.cli.main import cli


class TestChecksumIntegration:
    """Test class for checksum CLI integration."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def _create_mock_container(self):
        """Create a mock service container for IoC pattern."""
        mock_service = Mock()
        mock_container = Mock()
        mock_container.resolve.return_value = mock_service
        mock_service_container = Mock()
        mock_service_container.get_container.return_value = mock_container
        return mock_service_container

    def test_checksum_calculate_json_output(self):
        """Test checksum calculate command with JSON output."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "test"],
            obj={"container": mock_container},
        )

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
        mock_container = self._create_mock_container()
        # First calculate a checksum
        calc_result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "test"],
            obj={"container": mock_container},
        )
        assert calc_result.exit_code == 0

        calc_data = json.loads(calc_result.output)
        checksum = calc_data["data"]["checksum"]

        # Then validate it
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "test", checksum],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)

        assert output_data["success"] is True
        assert output_data["data"]["input"] == "test"

    def test_checksum_validate_invalid_checksum(self):
        """Test checksum validate command with invalid checksum."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "test", "XX"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        output = result.output

        assert '"input": "test"' in output
        assert '"expected_checksum": "XX"' in output
        assert '"is_valid": false' in output

    def test_checksum_validate_crc32_algorithm(self):
        """Test checksum validate command with CRC32 algorithm."""
        mock_container = self._create_mock_container()
        # First calculate a CRC32 checksum
        calc_result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "test", "--algorithm", "crc32"],
            obj={"container": mock_container},
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
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        output = result.output

        assert '"is_valid": true' in output

    def test_checksum_validate_json_output(self):
        """Test checksum validate command with JSON output."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "test", "XX"],
            obj={"container": mock_container},
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
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli, ["telegram", "checksum", "--help"], obj={"container": mock_container}
        )

        assert result.exit_code == 0
        output = result.output

        assert "Perform checksum calculation and validation operations" in output
        assert "calculate" in output
        assert "validate" in output

    def test_checksum_calculate_help(self):
        """Test checksum calculate help command."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "--help"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        output = result.output

        assert "Calculate checksum for given data string" in output
        assert "--algorithm" in output

    def test_checksum_validate_help(self):
        """Test checksum validate help command."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "--help"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        output = result.output

        assert "Validate data against expected checksum" in output
        assert "--algorithm" in output

    def test_checksum_calculate_empty_string(self):
        """Test checksum calculate with empty string."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 2
        output = result.output

        assert "Usage: cli telegram checksum calculate [OPTIONS] DATA" in output

    def test_checksum_validate_empty_string(self):
        """Test checksum validate with empty string."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "", "AA"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        output = result.output

        assert '"is_valid": true' in output

    def test_algorithm_parameter_validation(self):
        """Test that algorithm parameter accepts only valid values."""
        mock_container = self._create_mock_container()
        # Test invalid algorithm
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "test", "--algorithm", "invalid"],
            obj={"container": mock_container},
        )

        assert result.exit_code != 0
        assert "Invalid value for '--algorithm'" in result.output

    def test_missing_arguments(self):
        """Test commands with missing required arguments."""
        mock_container = self._create_mock_container()
        # Missing data argument for calculate
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate"],
            obj={"container": mock_container},
        )
        assert result.exit_code != 0

        # Missing expected_checksum argument for validate
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "test"],
            obj={"container": mock_container},
        )
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
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", test_data],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0
        assert f'"input": "{test_data}"' in result.output
        assert '"checksum":' in result.output

    @pytest.mark.parametrize("algorithm", ["simple", "crc32"])
    def test_checksum_roundtrip(self, algorithm):
        """Test calculate then validate roundtrip for both algorithms."""
        mock_container = self._create_mock_container()
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
            obj={"container": mock_container},
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
            obj={"container": mock_container},
        )
        assert validate_result.exit_code == 0

        validate_data = json.loads(validate_result.output)
        assert validate_data["data"]["is_valid"] is True

    def test_integration_with_telegram_parse(self):
        """Test integration concept - checksum could be used with telegram parsing."""
        # This tests that the checksum commands are available alongside other commands
        mock_container = self._create_mock_container()

        # First test that checksum commands exist
        result = self.runner.invoke(
            cli, ["telegram", "--help"], obj={"container": mock_container}
        )
        assert result.exit_code == 0
        assert "checksum" in result.output

        # Test that other command groups still exist
        assert "telegram" in result.output
        assert "module" in result.output

    def test_consistent_output_format(self):
        """Test that output format is consistent with other CLI commands."""
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "calculate", "test"],
            obj={"container": mock_container},
        )

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
        mock_container = self._create_mock_container()
        result = self.runner.invoke(
            cli,
            ["telegram", "checksum", "validate", "test", "invalid"],
            obj={"container": mock_container},
        )

        assert result.exit_code == 0  # Validation failure is not a CLI error
        output_data = json.loads(result.output)

        assert "success" in output_data
        assert output_data["data"]["is_valid"] is False
