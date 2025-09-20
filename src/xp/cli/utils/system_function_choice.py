import click

from xp.models.system_function import SystemFunction


# noinspection DuplicatedCode
class SystemFunctionChoice(click.ParamType):
    name = "system_function"

    def __init__(self):
        self.choices = [key.lower() for key in SystemFunction.__members__.keys()]

    def convert(self, value, param, ctx):
        if value is None:
            return value

        # Convert to lower for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            # Return the actual enum member
            return SystemFunction[normalized_value.upper()] # type: ignore

        # If not found, show error with available choices
        self.fail(f'{value!r} is not a valid choice. '
                  f'Choose from: {", ".join(self.choices)}',
                  param, ctx)

SYSTEM_FUNCTION = SystemFunctionChoice()
