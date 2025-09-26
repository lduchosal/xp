import click
from typing import Any, Optional


class SerialNumberParamType(click.ParamType):
    name = "serial_number"

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Optional[str]:
        if value is None:
            return None

        # Convert to string if not already
        str_value = str(value)

        # Check if contains only numeric characters (empty string should be treated as "0")
        if not str_value.isdigit() and str_value != "":
            self.fail(f"{value!r} contains non-numeric characters", param, ctx)

        # Handle empty string as zero
        if str_value == "":
            str_value = "0"

        # Check length constraints
        if len(str_value) > 10:
            self.fail(f"{value!r} is longer than 10 characters", param, ctx)

        # Pad left with zeros if length < 10
        return str_value.zfill(10)


SERIAL = SerialNumberParamType()
