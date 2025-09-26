"""Conbus link number CLI commands."""

import json

import click

from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.serial_number_type import SERIAL
from ...services.conbus_linknumber_service import ConbusLinknumberService
from ...services.telegram_link_number_service import LinkNumberError


@click.command("linknumber", short_help="Set link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=click.IntRange(0, 99))
@connection_command()
@handle_service_errors(LinkNumberError)
def conbus_linknumber_command(serial_number: str, link_number: int) -> None:
    """
    Set the link number for a specific module.

    SERIAL_NUMBER: 10-digit module serial number
    LINK_NUMBER: Link number to set (0-99)

    Examples:

    \b
        xp conbus linknumber 0020045057 25
    """
    service = ConbusLinknumberService()

    with service:
        response = service.set_linknumber(serial_number, link_number)
        click.echo(json.dumps(response.to_dict(), indent=2))