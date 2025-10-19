"""Conbus client operations CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_datapoint

# Import will be handled by conbus.py registration
from xp.cli.utils.datapoint_type_choice import DATAPOINT
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.conbus.conbus_datapoint import ConbusDatapointResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.services.conbus.conbus_datapoint_queryall_service import (
    ConbusDatapointQueryAllService,
)
from xp.services.conbus.conbus_datapoint_service import (
    ConbusDatapointService,
)


@click.command("query")
@click.argument("datapoint", type=DATAPOINT)
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def query_datapoint(ctx: Context, serial_number: str, datapoint: DataPointType) -> None:
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
    service = ctx.obj.get("container").get_container().resolve(ConbusDatapointService)

    def on_finish(service_response: ConbusDatapointResponse) -> None:
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    # Send telegram
    with service:
        service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=datapoint,
            finish_callback=on_finish,
        )


# Add the single datapoint query command to the group
conbus_datapoint.add_command(query_datapoint)


@conbus_datapoint.command("all", short_help="Query all datapoints from a module")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def query_all_datapoints(ctx: Context, serial_number: str) -> None:
    """
    Query all datapoints from a specific module.

    Examples:

    \b
        xp conbus datapoint all 0123450001
    """
    service = (
        ctx.obj.get("container").get_container().resolve(ConbusDatapointQueryAllService)
    )

    def on_finish(service_response: ConbusDatapointResponse) -> None:
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    def on_progress(reply_telegram: ReplyTelegram) -> None:
        click.echo(json.dumps(reply_telegram.to_dict(), indent=2))

    with service:
        service.query_all_datapoints(
            serial_number=serial_number,
            finish_callback=on_finish,
            progress_callback=on_progress,
        )
