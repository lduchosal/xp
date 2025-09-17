import click

class SerialNumberParamType(click.ParamType):
    name = "serial_number"

    def convert(self, value, param, ctx):
        if isinstance(value, str):
            return value

        if len(value) > 10:
            self.fail(f"{value!r} is not a valid serial_number", param, ctx)
        elif len(value) < 10:
            return int(value, 10)
        return value

SERIAL = SerialNumberParamType()