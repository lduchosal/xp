"""Conbus client operations CLI commands."""

import json

import click

# Import will be handled by conbus.py registration
from ..utils.datapoint_type_choice import DATAPOINT
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.serial_number_type import SERIAL
from .conbus import conbus_datapoint
from ...models.datapoint_type import DataPointType
from ...services.conbus_datapoint_service import (
    ConbusDatapointService,
    ConbusDatapointError,
)


@click.command("query")
@click.argument("datapoint", type=DATAPOINT)
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def query_datapoint(serial_number: str, datapoint: DataPointType) -> None:
    """
    Query a specific datapoint from Conbus server.

    Examples:

    \b
        xp conbus datapoint query version 0012345011
        xp conbus datapoint query voltage 0012345011
        xp conbus datapoint query temperature 0012345011
        xp conbus datapoint query current 0012345011
        xp conbus datapoint query humidity 0012345011
    """
    service = ConbusDatapointService()

    # Send telegram
    with service:
        response = service.query_datapoint(
            datapoint_type=datapoint, serial_number=serial_number
        )

    click.echo(json.dumps(response.to_dict(), indent=2))


# Add the single datapoint query command to the group
conbus_datapoint.add_command(query_datapoint)


@conbus_datapoint.command("all", short_help="Query all datapoints from a module")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def query_all_datapoints(serial_number: str) -> None:
    """
    Query all datapoints from a specific module.

    Examples:

    \b
        xp conbus datapoint all 0123450001
    """
    service = ConbusDatapointService()

    with service:
        response = service.query_all_datapoints(serial_number=serial_number)

    click.echo(json.dumps(response.to_dict(), indent=2))
