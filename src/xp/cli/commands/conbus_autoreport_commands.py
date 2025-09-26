"""Conbus auto report CLI commands."""

import json
import click

from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from .conbus import conbus_autoreport
from ..utils.serial_number_type import SERIAL
from ...services.conbus_autoreport_service import (
    ConbusAutoreportService,
    ConbusAutoreportError,
)


@conbus_autoreport.command("get", short_help="Get auto report status for a module")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusAutoreportError)
def get_autoreport_command(serial_number: str) -> None:
    """
    Get the current auto report status for a specific module.

    SERIAL_NUMBER: 10-digit module serial number

    Examples:

    \b
        xp conbus autoreport get 0123450001
    """
    service = ConbusAutoreportService()

    with service:
        response = service.get_autoreport_status(serial_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_autoreport.command("set", short_help="Set auto report status for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("status", type=click.Choice(["on", "off"], case_sensitive=False))
@connection_command()
@handle_service_errors(ConbusAutoreportError)
def set_autoreport_command(serial_number: str, status: str) -> None:
    """
    Set the auto report status for a specific module.

    SERIAL_NUMBER: 10-digit module serial number
    STATUS: Auto report status - either 'on' or 'off'

    Examples:

    \b
        xp conbus autoreport set 0123450001 on
        xp conbus autoreport set 0123450001 off
    """
    service = ConbusAutoreportService()
    status_bool = status.lower() == "on"

    with service:
        response = service.set_autoreport_status(serial_number, status_bool)
        click.echo(json.dumps(response.to_dict(), indent=2))
