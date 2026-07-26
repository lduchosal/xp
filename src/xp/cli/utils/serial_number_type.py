# Copyright (c) 2025 ldvchosal
"""Click parameter type for serial number validation."""

import click

SERIAL_NUMBER_LENGTH = 10


class SerialNumberParamType(click.ParamType):
    """Click parameter type for validating and formatting serial numbers.

    Attributes:
        name: The parameter type name.

    """

    name = "serial_number"

    def convert(
        self, value: object, param: click.Parameter | None, ctx: click.Context | None
    ) -> str | None:
        """Convert and validate serial number input.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            10-character zero-padded serial number string, or None if input is None.

        """
        if value is None:
            return None

        # Convert to string if not already
        str_value = str(value)

        # Check that it only contains numeric characters
        # (empty string should be treated as "0")
        if not str_value.isdigit() and str_value:
            self.fail(f"{value!r} contains non-numeric characters", param, ctx)

        # Handle empty string as zero
        if not str_value:
            str_value = "0"

        # Check length constraints
        if len(str_value) > SERIAL_NUMBER_LENGTH:
            self.fail(f"{value!r} is longer than 10 characters", param, ctx)

        # Pad left with zeros if length < 10
        return str_value.zfill(SERIAL_NUMBER_LENGTH)


SERIAL = SerialNumberParamType()
