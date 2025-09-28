import click
from typing import Any, Optional


class XpModuleTypeChoice(click.ParamType):
    name = "xpmoduletype"

    def __init__(self) -> None:
        self.choices = ["xp20", "xp24", "xp31", "xp33"]

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Any:
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
