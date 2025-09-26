import pytest
import click
from click.testing import CliRunner
from xp.cli.utils.serial_number_type import SerialNumberParamType, SERIAL


class TestSerialNumberParamType:
    def setup_method(self):
        self.param_type = SerialNumberParamType()
        self.param = None
        self.ctx = None

    def test_valid_10_digit_serial(self):
        result = self.param_type.convert("1234567890", self.param, self.ctx)
        assert result == "1234567890"

    def test_short_serial_padded_with_zeros(self):
        result = self.param_type.convert("123", self.param, self.ctx)
        assert result == "0000000123"

    def test_single_digit_serial(self):
        result = self.param_type.convert("5", self.param, self.ctx)
        assert result == "0000000005"

    def test_empty_string_padded(self):
        result = self.param_type.convert("", self.param, self.ctx)
        assert result == "0000000000"

    def test_integer_input_converted(self):
        result = self.param_type.convert(123, self.param, self.ctx)
        assert result == "0000000123"

    def test_none_value_returns_none(self):
        result = self.param_type.convert(None, self.param, self.ctx)
        assert result is None

    def test_serial_too_long_raises_error(self):
        with pytest.raises(click.BadParameter, match="longer than 10 characters"):
            self.param_type.convert("12345678901", self.param, self.ctx)

    def test_non_numeric_characters_raises_error(self):
        with pytest.raises(click.BadParameter, match="contains non-numeric characters"):
            self.param_type.convert("123abc", self.param, self.ctx)

    def test_serial_with_spaces_raises_error(self):
        with pytest.raises(click.BadParameter, match="contains non-numeric characters"):
            self.param_type.convert("123 456", self.param, self.ctx)

    def test_serial_with_special_chars_raises_error(self):
        with pytest.raises(click.BadParameter, match="contains non-numeric characters"):
            self.param_type.convert("123-456", self.param, self.ctx)


class TestSerialNumberTypeInCommand:
    def test_serial_type_in_click_command(self):
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
