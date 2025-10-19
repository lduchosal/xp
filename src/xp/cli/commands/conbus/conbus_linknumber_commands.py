"""Conbus link number CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_linknumber
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.services.conbus.conbus_linknumber_get_service import ConbusLinknumberGetService
from xp.services.conbus.conbus_linknumber_set_service import ConbusLinknumberSetService


@conbus_linknumber.command("set", short_help="Set link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=click.IntRange(0, 99))
@click.pass_context
@connection_command()
def set_linknumber_command(
    ctx: click.Context, serial_number: str, link_number: int
) -> None:
    """
    Set the link number for a specific module.

    SERIAL_NUMBER: 10-digit module serial number
    LINK_NUMBER: Link number to set (0-99)

    Examples:

    \b
        xp conbus linknumber set 0123450001 25
    """
    service = (
        ctx.obj.get("container").get_container().resolve(ConbusLinknumberSetService)
    )

    def on_finish(response: ConbusLinknumberResponse) -> None:
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.set_linknumber(
            serial_number=serial_number,
            link_number=link_number,
            finish_callback=on_finish,
        )


@conbus_linknumber.command("get", short_help="Get link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def get_linknumber_command(ctx: click.Context, serial_number: str) -> None:
    """
    Get the current link number for a specific module.

    SERIAL_NUMBER: 10-digit module serial number

    Examples:

    \b
        xp conbus linknumber get 0123450001
    """
    service = (
        ctx.obj.get("container").get_container().resolve(ConbusLinknumberGetService)
    )

    def on_finish(response: ConbusLinknumberResponse) -> None:
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.get_linknumber(
            serial_number=serial_number,
            finish_callback=on_finish,
        )
