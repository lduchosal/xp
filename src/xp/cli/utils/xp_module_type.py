"""Click parameter type for XP module type validation."""

from typing import Any, Optional

import click


class XpModuleTypeChoice(click.ParamType):
    """Click parameter type for validating XP module types.

    Attributes:
        name: The parameter type name.
        choices: List of valid module type strings.
    """

    name = "xpmoduletype"

    def __init__(self) -> None:
        """Initialize the XpModuleTypeChoice parameter type."""
        self.choices = ["xp20", "xp24", "xp31", "xp33"]

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Any:
        """Convert and validate XP module type input.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            Lowercase module type string if valid, None if input is None.
        """
        if value is None:
            return value

        # Convert to lower for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            return normalized_value

        # If not found, show error with available choices
        choices_list = "\n".join(f" - {choice}" for choice in sorted(self.choices))
        self.fail(
            f"{value!r} is not a valid choice. " f"Choose from:\n{choices_list}",
            param,
            ctx,
        )


XP_MODULE_TYPE = XpModuleTypeChoice()
