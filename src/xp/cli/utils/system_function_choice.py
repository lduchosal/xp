"""Click parameter type for SystemFunction enum validation."""

from typing import Any, Optional

import click

from xp.models.telegram.system_function import SystemFunction


# noinspection DuplicatedCode
class SystemFunctionChoice(click.ParamType):
    """Click parameter type for validating SystemFunction enum values.

    Attributes:
        name: The parameter type name.
        choices: List of valid choice strings.
    """

    name = "system_function"

    def __init__(self) -> None:
        """Initialize the SystemFunctionChoice parameter type."""
        self.choices = [key.lower() for key in SystemFunction.__members__.keys()]

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Any:
        """Convert and validate input to SystemFunction enum.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            SystemFunction enum member if valid, None if input is None.
        """
        if value is None:
            return value

        # Convert to lower for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            # Return the actual enum member
            return SystemFunction[normalized_value.upper()]

        # If not found, show error with available choices
        self.fail(
            f"{value!r} is not a valid choice. "
            f'Choose from: {", ".join(self.choices)}',
            param,
            ctx,
        )


SYSTEM_FUNCTION = SystemFunctionChoice()
