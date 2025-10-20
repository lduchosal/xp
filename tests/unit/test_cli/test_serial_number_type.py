"""Unit tests for serial number parameter type."""

import click
import pytest
from click.testing import CliRunner

from xp.cli.utils.serial_number_type import SERIAL, SerialNumberParamType


class TestSerialNumberParamType:
    """Test cases for SerialNumberParamType parameter type."""

    def setup_method(self):
        """Set up test fixtures."""
        self.param_type = SerialNumberParamType()
        self.param = None
        self.ctx = None

    def test_valid_10_digit_serial(self):
        """Test valid 10-digit serial number."""
        result = self.param_type.convert("1234567890", self.param, self.ctx)
        assert result == "1234567890"

    def test_short_serial_padded_with_zeros(self):
        """Test short serial number is padded with zeros."""
        result = self.param_type.convert("123", self.param, self.ctx)
        assert result == "0000000123"

    def test_single_digit_serial(self):
        """Test single digit serial number."""
        result = self.param_type.convert("5", self.param, self.ctx)
        assert result == "0000000005"

    def test_empty_string_padded(self):
        """Test empty string is padded with zeros."""
        result = self.param_type.convert("", self.param, self.ctx)
        assert result == "0000000000"

    def test_integer_input_converted(self):
        """Test integer input is converted to string."""
        result = self.param_type.convert(123, self.param, self.ctx)
        assert result == "0000000123"

    def test_none_value_returns_none(self):
        """Test None value returns None."""
        result = self.param_type.convert(None, self.param, self.ctx)
        assert result is None

    def test_serial_too_long_raises_error(self):
        """Test serial number too long raises error."""
        with pytest.raises(click.BadParameter, match="longer than 10 characters"):
            self.param_type.convert("12345678901", self.param, self.ctx)

    def test_non_numeric_characters_raises_error(self):
        """Test non-numeric characters raise error."""
        with pytest.raises(click.BadParameter, match="contains non-numeric characters"):
            self.param_type.convert("123abc", self.param, self.ctx)

    def test_serial_with_spaces_raises_error(self):
        """Test serial with spaces raises error."""
        with pytest.raises(click.BadParameter, match="contains non-numeric characters"):
            self.param_type.convert("123 456", self.param, self.ctx)

    def test_serial_with_special_chars_raises_error(self):
        """Test serial with special characters raises error."""
        with pytest.raises(click.BadParameter, match="contains non-numeric characters"):
            self.param_type.convert("123-456", self.param, self.ctx)


class TestSerialNumberTypeInCommand:
    """Test cases for using SERIAL type in Click commands."""

    def test_serial_type_in_click_command(self):
        """Test SERIAL type integration with Click commands."""

        @click.command()
        @click.argument("serial_number", type=SERIAL)
        def test_command(serial_number):
            click.echo(f"Serial: {serial_number}")

        runner = CliRunner()

        # Test valid short serial
        result = runner.invoke(test_command, ["123"])
        assert result.exit_code == 0
        assert "Serial: 0000000123" in result.output

        # Test valid 10-digit serial
        result = runner.invoke(test_command, ["1234567890"])
        assert result.exit_code == 0
        assert "Serial: 1234567890" in result.output

        # Test invalid serial (too long)
        result = runner.invoke(test_command, ["12345678901"])
        assert result.exit_code != 0
        assert "longer than 10 characters" in result.output

        # Test invalid serial (non-numeric)
        result = runner.invoke(test_command, ["123abc"])
        assert result.exit_code != 0
        assert "contains non-numeric characters" in result.output
