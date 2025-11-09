"""Click parameter type for ModuleTypeCode enum validation."""

from typing import Any, Optional

import click

from xp.models.telegram.module_type_code import ModuleTypeCode


class ModuleTypeChoice(click.ParamType):
    """Click parameter type for validating ModuleTypeCode enum values.

    Attributes:
        name: The parameter type name.
        choices: List of valid choice strings.
    """

    name = "module_type"

    def __init__(self) -> None:
        """Initialize the ModuleTypeChoice parameter type."""
        self.choices = [key for key in ModuleTypeCode.__members__.keys()]

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> int:
        """Convert and validate input to ModuleTypeCode value.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            Module type code integer value if valid.
        """
        if value is None:
            self.fail("Module type is required", param, ctx)

        # Convert to upper for comparison
        normalized_value = value.upper()

        if normalized_value in self.choices:
            # Return the actual enum value (integer)
            return ModuleTypeCode[normalized_value].value

        # If not found, show error with available choices
        choices_list = "\n".join(f" - {choice}" for choice in sorted(self.choices))
        self.fail(
            f"{value!r} is not a valid module type. " f"Choose from:\n{choices_list}",
            param,
            ctx,
        )


MODULE_TYPE = ModuleTypeChoice()
