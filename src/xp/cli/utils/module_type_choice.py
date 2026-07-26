# Copyright (c) 2025 ldvchosal
"""Click parameter type for ModuleTypeCode enum validation."""

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
        self.choices = list(ModuleTypeCode.__members__.keys())

    def convert(
        self, value: object, param: click.Parameter | None, ctx: click.Context | None
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
        normalized_value = str(value).upper()

        if normalized_value not in self.choices:
            # If not found, show error with available choices
            choices_list = "\n".join(f" - {choice}" for choice in sorted(self.choices))
            self.fail(
                f"{value!r} is not a valid module type. Choose from:\n{choices_list}",
                param,
                ctx,
            )

        # Return the actual enum value (integer)
        return ModuleTypeCode[normalized_value].value


MODULE_TYPE = ModuleTypeChoice()
