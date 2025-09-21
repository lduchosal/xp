"""Conbus client operations CLI commands."""

import json

import click

from .conbus import conbus
from ..utils.datapoint_type_choice import DATAPOINT
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.formatters import OutputFormatter
from ..utils.serial_number_type import SERIAL
from ...models.datapoint_type import DataPointType
from ...services.conbus_datapoint_service import (
    ConbusDatapointService,
    ConbusDatapointError,
)


@conbus.command("datapoint")
@click.argument("datapoint", type=DATAPOINT)
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def datapoint_telegram(serial_number: str, datapoint: DataPointType):
    """
    Send telegram to Conbus server.

    Examples:

    \b
        xp conbus datapoint version 0012345011
        xp conbus datapoint voltage 0012345011
        xp conbus datapoint temperature 0012345011
        xp conbus datapoint current 0012345011
        xp conbus datapoint humidity 0012345011
    """
    service = ConbusDatapointService()
    formatter = OutputFormatter(True)

    # Validate arguments
    if serial_number is None:
        error_response = formatter.error_response("serial_number is required")
        click.echo(error_response)
        raise SystemExit(1)

    if datapoint is None:
        error_response = formatter.error_response("Datapoint is required")
        click.echo(error_response)
        raise SystemExit(1)

    # Send telegram
    with service:
        response = service.send_telegram(datapoint_type=datapoint, serial_number=serial_number)

    click.echo(json.dumps(response.to_dict(), indent=2))
