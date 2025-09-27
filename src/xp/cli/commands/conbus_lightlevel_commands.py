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
@click.argument("link_number", type=int)
@click.argument("level", type=int)
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_set(serial_number: str, link_number: int, level: int) -> None:
    """Set light level for link_number on XP module serial_number

    Examples:

    \b
        xp conbus lightlevel set 0020045057 2 50   # Set link 2 to 50%
        xp conbus lightlevel set 0011223344 0 100  # Set link 0 to 100%
    """
    service = ConbusLightlevelService()

    with service:
        response = service.set_lightlevel(serial_number, link_number, level)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_lightlevel.command("off")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=int)
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_off(serial_number: str, link_number: int) -> None:
    """Turn off light for link_number on XP module serial_number (set level to 0)

    Examples:

    \b
        xp conbus lightlevel off 0020045057 2   # Turn off link 2
        xp conbus lightlevel off 0011223344 0   # Turn off link 0
    """
    service = ConbusLightlevelService()

    with service:
        response = service.turn_off(serial_number, link_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_lightlevel.command("on")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=int)
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_on(serial_number: str, link_number: int) -> None:
    """Turn on light for link_number on XP module serial_number (set level to 80%)

    Examples:

    \b
        xp conbus lightlevel on 0020045057 2   # Turn on link 2 (80%)
        xp conbus lightlevel on 0011223344 0   # Turn on link 0 (80%)
    """
    service = ConbusLightlevelService()

    with service:
        response = service.turn_on(serial_number, link_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_lightlevel.command("get")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=int)
@connection_command()
@handle_service_errors(ConbusLightlevelError)
def xp_lightlevel_get(serial_number: str, link_number: int) -> None:
    """Get current light level for link_number on XP module serial_number

    Examples:

    \b
        xp conbus lightlevel get 0020045057 2   # Get light level for link 2
        xp conbus lightlevel get 0011223344 0   # Get light level for link 0
    """
    service = ConbusLightlevelService()

    with service:
        response = service.get_lightlevel(serial_number, link_number)
        click.echo(json.dumps(response.to_dict(), indent=2))
