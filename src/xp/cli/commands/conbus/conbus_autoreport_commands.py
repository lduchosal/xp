"""Conbus auto report CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_autoreport
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.conbus.conbus_autoreport import ConbusAutoreportResponse
from xp.services.conbus.conbus_autoreport_get_service import (
    ConbusAutoreportGetService,
)
from xp.services.conbus.conbus_autoreport_set_service import ConbusAutoreportSetService


@conbus_autoreport.command("get", short_help="Get auto report status for a module")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@click.pass_context
def get_autoreport_command(ctx: Context, serial_number: str) -> None:
    """
    Get the current auto report status for a specific module.

    SERIAL_NUMBER: 10-digit module serial number

    Examples:

    \b
        xp conbus autoreport get 0123450001
    """
    # Get service from container
    service = (
        ctx.obj.get("container").get_container().resolve(ConbusAutoreportGetService)
    )

    def on_finish(service_response: ConbusAutoreportResponse) -> None:
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    with service:
        service.get_autoreport_status(
            serial_number=serial_number,
            finish_callback=on_finish,
        )


@conbus_autoreport.command("set", short_help="Set auto report status for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("status", type=click.Choice(["on", "off"], case_sensitive=False))
@connection_command()
@click.pass_context
def set_autoreport_command(ctx: Context, serial_number: str, status: str) -> None:
    """
    Set the auto report status for a specific module.

    SERIAL_NUMBER: 10-digit module serial number
    STATUS: Auto report status - either 'on' or 'off'

    Examples:

    \b
        xp conbus autoreport set 0123450001 on
        xp conbus autoreport set 0123450001 off
    """
    # Get service from container
    service = (
        ctx.obj.get("container").get_container().resolve(ConbusAutoreportSetService)
    )
    status_bool = status.lower() == "on"

    def on_finish(service_response: ConbusAutoreportResponse) -> None:
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    with service:
        service.set_autoreport_status(
            serial_number=serial_number, status=status_bool, status_callback=on_finish
        )
