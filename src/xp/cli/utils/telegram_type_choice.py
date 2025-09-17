import click

from xp.models import TelegramType


class TelegramTypeChoice(click.ParamType):
    name = "telegram_type"

    def __init__(self):
        self.choices = [key.lower() for key in TelegramType.__members__.keys()]

    def convert(self, value, param, ctx):
        if value is None:
            return value

        # Convert to lowercase for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            # Return the actual enum member
            return TelegramType[normalized_value]

        # If not found, show error with available choices
        self.fail(f'{value!r} is not a valid choice. '
                  f'Choose from: {", ".join(self.choices)}',
                  param, ctx)

TELEGRAM = TelegramTypeChoice()
