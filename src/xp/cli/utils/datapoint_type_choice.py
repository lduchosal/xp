# Copyright (c) 2025 ldvchosal
"""Click parameter type for DataPointType enum validation."""

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
        self.choices = [key.lower() for key in DataPointType.__members__]

    def convert(
        self, value: object, param: click.Parameter | None, ctx: click.Context | None
    ) -> DataPointType | None:
        """Convert and validate input to DataPointType enum.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            DataPointType enum member if valid, None if input is None.

        """
        if value is None:
            return None

        # Convert to lower for comparison
        normalized_value = str(value).lower()

        if normalized_value not in self.choices:
            # If not found, show error with available choices
            choices_list = "\n".join(f" - {choice}" for choice in sorted(self.choices))
            self.fail(
                f"{value!r} is not a valid choice. Choose from:\n{choices_list}",
                param,
                ctx,
            )

        # Return the actual enum member
        return DataPointType[normalized_value.upper()]


DATAPOINT = DatapointTypeChoice()
