import click

from xp.models import DatapointTypeName


class DatapointTypeNameChoice(click.ParamType):
    name = "telegram_type"

    def __init__(self):
        self.choices = [key.lower() for key in DatapointTypeName.__members__.keys()]

    def convert(self, value, param, ctx):
        if value is None:
            return value

        # Convert to lower for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            # Return the actual enum member
            return DatapointTypeName[normalized_value.upper()]

        # If not found, show error with available choices
        self.fail(f'{value!r} is not a valid choice. '
                  f'Choose from: {", ".join(self.choices)}',
                  param, ctx)

DATAPOINT = DatapointTypeNameChoice()
