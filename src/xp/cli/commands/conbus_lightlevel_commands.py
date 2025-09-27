"""Conbus lightlevel operations CLI commands."""

import click
import json

from ..utils.serial_number_type import SERIAL
from ...services.conbus_lightlevel_service import (
    ConbusLightlevelService,
    ConbusLightlevelError,
)
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from .conbus import conbus_lightlevel


@conbus_lightlevel.command("set")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@click.argument("level", type=click.IntRange(0, 100))
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_set(serial_number: str, output_number: int, level: int) -> None:
    """Set light level for output_number on XP module serial_number

    Examples:

    \b
        xp conbus lightlevel set 0123450001 2 50   # Set output 2 to 50%
        xp conbus lightlevel set 0011223344 0 100  # Set output 0 to 100%
    """
    service = ConbusLightlevelService()

    with service:
        response = service.set_lightlevel(serial_number, output_number, level)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_lightlevel.command("off")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_off(serial_number: str, output_number: int) -> None:
    """Turn off light for output_number on XP module serial_number (set level to 0)

    Examples:

    \b
        xp conbus lightlevel off 0123450001 2   # Turn off output 2
        xp conbus lightlevel off 0011223344 0   # Turn off output 0
    """
    service = ConbusLightlevelService()

    with service:
        response = service.turn_off(serial_number, output_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_lightlevel.command("on")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_on(serial_number: str, output_number: int) -> None:
    """Turn on light for output_number on XP module serial_number (set level to 80%)

    Examples:

    \b
        xp conbus lightlevel on 0123450001 2   # Turn on output 2 (80%)
        xp conbus lightlevel on 0011223344 0   # Turn on output 0 (80%)
    """
    service = ConbusLightlevelService()

    with service:
        response = service.turn_on(serial_number, output_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_lightlevel.command("get")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_get(serial_number: str, output_number: int) -> None:
    """Get current light level for output_number on XP module serial_number

    Examples:

    \b
        xp conbus lightlevel get 0123450001 2   # Get light level for output 2
        xp conbus lightlevel get 0011223344 0   # Get light level for output 0
    """
    service = ConbusLightlevelService()

    with service:
        response = service.get_lightlevel(serial_number, output_number)
        click.echo(json.dumps(response.to_dict(), indent=2))
