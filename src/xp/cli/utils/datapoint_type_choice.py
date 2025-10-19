"""Click parameter type for DataPointType enum validation."""

from typing import Any, Optional

import click

from xp.models.telegram.datapoint_type import DataPointType


# noinspection DuplicatedCode
class DatapointTypeChoice(click.ParamType):
    """Click parameter type for validating DataPointType enum values.

    Attributes:
        name: The parameter type name.
        choices: List of valid choice strings.
    """

    name = "telegram_type"

    def __init__(self) -> None:
        """Initialize the DatapointTypeChoice parameter type."""
        self.choices = [key.lower() for key in DataPointType.__members__.keys()]

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Any:
        """Convert and validate input to DataPointType enum.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            DataPointType enum member if valid, None if input is None.
        """
        if value is None:
            return value

        # Convert to lower for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            # Return the actual enum member
            return DataPointType[normalized_value.upper()]

        # If not found, show error with available choices
        choices_list = "\n".join(f" - {choice}" for choice in sorted(self.choices))
        self.fail(
            f"{value!r} is not a valid choice. " f"Choose from:\n{choices_list}",
            param,
            ctx,
        )


DATAPOINT = DatapointTypeChoice()
