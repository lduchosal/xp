import click

from xp.models.datapoint_type import DataPointType


# noinspection DuplicatedCode
class DatapointTypeChoice(click.ParamType):
    name = "telegram_type"

    def __init__(self):
        self.choices = [key.lower() for key in DataPointType.__members__.keys()]

    def convert(self, value, param, ctx):
        if value is None:
            return value

        # Convert to lower for comparison
        normalized_value = value.lower()

        if normalized_value in self.choices:
            # Return the actual enum member
            return DataPointType[normalized_value.upper()] # type: ignore

        # If not found, show error with available choices
        self.fail(f'{value!r} is not a valid choice. '
                  f'Choose from: {", ".join(self.choices)}',
                  param, ctx)

DATAPOINT = DatapointTypeChoice()
