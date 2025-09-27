"""Conbus link number CLI commands."""

import json
import click

from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from .conbus import conbus_linknumber
from ..utils.serial_number_type import SERIAL
from ...services.conbus_linknumber_service import ConbusLinknumberService
from ...services.telegram_link_number_service import LinkNumberError


@conbus_linknumber.command("set", short_help="Set link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=click.IntRange(0, 99))
@connection_command()
@handle_service_errors(LinkNumberError)
def set_linknumber_command(serial_number: str, link_number: int) -> None:
    """
    Set the link number for a specific module.

    SERIAL_NUMBER: 10-digit module serial number
    LINK_NUMBER: Link number to set (0-99)

    Examples:

    \b
        xp conbus linknumber set 0123450001 25
    """
    service = ConbusLinknumberService()

    with service:
        response = service.set_linknumber(serial_number, link_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_linknumber.command("get", short_help="Get link number for a module")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(LinkNumberError)
def get_linknumber_command(serial_number: str) -> None:
    """
    Get the current link number for a specific module.

    SERIAL_NUMBER: 10-digit module serial number

    Examples:

    \b
        xp conbus linknumber get 0123450001
    """
    service = ConbusLinknumberService()

    with service:
        response = service.get_linknumber(serial_number)
        click.echo(json.dumps(response.to_dict(), indent=2))
