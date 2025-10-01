"""Tests for datapoint type choice parameter type."""

import click
import pytest
from click.testing import CliRunner

from xp.cli.utils.datapoint_type_choice import DATAPOINT, DatapointTypeChoice
from xp.models.telegram.datapoint_type import DataPointType


class TestDatapointTypeChoice:
    """Test DatapointTypeChoice class."""

    def test_init(self):
        """Test initialization creates choices from enum."""
        choice = DatapointTypeChoice()
        assert choice.name == "telegram_type"
        assert isinstance(choice.choices, list)
        assert len(choice.choices) > 0
        assert all(isinstance(c, str) for c in choice.choices)

    def test_convert_valid_value(self):
        """Test converting valid value returns enum member."""
        choice = DatapointTypeChoice()
        # Get a valid choice from the enum
        valid_choice = list(DataPointType.__members__.keys())[0].lower()
        result = choice.convert(valid_choice, None, None)
        assert isinstance(result, DataPointType)

    def test_convert_none_value(self):
        """Test converting None returns None."""
        result = DatapointTypeChoice().convert(None, None, None)
        assert result is None

    def test_convert_case_insensitive(self):
        """Test conversion is case insensitive."""
        choice = DatapointTypeChoice()
        valid_choice = list(DataPointType.__members__.keys())[0]

        result_lower = choice.convert(valid_choice.lower(), None, None)
        result_upper = choice.convert(valid_choice.upper(), None, None)
        result_mixed = choice.convert(valid_choice.title(), None, None)

        assert result_lower == result_upper == result_mixed

    def test_convert_invalid_value_fails(self):
        """Test converting invalid value raises error."""
        choice = DatapointTypeChoice()

        with pytest.raises(click.exceptions.BadParameter) as exc_info:
            choice.convert("invalid_datapoint", None, None)

        error_msg = str(exc_info.value)
        assert "not a valid choice" in error_msg

    def test_module_level_constant(self):
        """Test DATAPOINT constant is properly initialized."""
        assert isinstance(DATAPOINT, DatapointTypeChoice)
        assert DATAPOINT.name == "telegram_type"

    def test_in_click_command(self):
        """Test DatapointTypeChoice works in Click command."""

        @click.command()
        @click.argument("datapoint", type=DATAPOINT)
        def test_cmd(datapoint):
            click.echo(f"Datapoint: {datapoint.name}")

        runner = CliRunner()
        valid_choice = list(DataPointType.__members__.keys())[0].lower()
        result = runner.invoke(test_cmd, [valid_choice])
        assert result.exit_code == 0
        assert "Datapoint:" in result.output

    def test_error_message_format(self):
        """Test error message shows formatted choices."""
        choice = DatapointTypeChoice()

        with pytest.raises(click.exceptions.BadParameter) as exc_info:
            choice.convert("bad_value", None, None)

        error_msg = str(exc_info.value)
        # Should have formatted list with " - " prefix
        assert " - " in error_msg or "Choose from" in error_msg
