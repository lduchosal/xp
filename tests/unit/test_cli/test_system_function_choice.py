"""Tests for system function choice parameter type."""

import click
import pytest
from click.testing import CliRunner

from xp.cli.utils.system_function_choice import SYSTEM_FUNCTION, SystemFunctionChoice
from xp.models.telegram.system_function import SystemFunction


class TestSystemFunctionChoice:
    """Test SystemFunctionChoice class."""

    def test_init(self):
        """Test initialization creates choices from enum."""
        choice = SystemFunctionChoice()
        assert choice.name == "system_function"
        assert isinstance(choice.choices, list)
        assert len(choice.choices) > 0
        assert all(isinstance(c, str) for c in choice.choices)

    def test_convert_valid_value(self):
        """Test converting valid value returns enum member."""
        choice = SystemFunctionChoice()
        # Get a valid choice from the enum
        valid_choice = list(SystemFunction.__members__.keys())[0].lower()
        result = choice.convert(valid_choice, None, None)
        assert isinstance(result, SystemFunction)

    def test_convert_none_value(self):
        """Test converting None returns None."""
        result = SystemFunctionChoice().convert(None, None, None)
        assert result is None

    def test_convert_case_insensitive(self):
        """Test conversion is case insensitive."""
        choice = SystemFunctionChoice()
        valid_choice = list(SystemFunction.__members__.keys())[0]

        result_lower = choice.convert(valid_choice.lower(), None, None)
        result_upper = choice.convert(valid_choice.upper(), None, None)
        result_mixed = choice.convert(valid_choice.title(), None, None)

        assert result_lower == result_upper == result_mixed

    def test_convert_invalid_value_fails(self):
        """Test converting invalid value raises error."""
        choice = SystemFunctionChoice()

        with pytest.raises(click.exceptions.BadParameter):
            choice.convert("invalid_function", None, None)

    def test_module_level_constant(self):
        """Test SYSTEM_FUNCTION constant is properly initialized."""
        assert isinstance(SYSTEM_FUNCTION, SystemFunctionChoice)
        assert SYSTEM_FUNCTION.name == "system_function"

    def test_in_click_command(self):
        """Test SystemFunctionChoice works in Click command."""

        @click.command()
        @click.argument("func", type=SYSTEM_FUNCTION)
        def test_cmd(func):
            click.echo(f"Function: {func.name}")

        runner = CliRunner()
        valid_choice = list(SystemFunction.__members__.keys())[0].lower()
        result = runner.invoke(test_cmd, [valid_choice])
        assert result.exit_code == 0
        assert "Function:" in result.output
