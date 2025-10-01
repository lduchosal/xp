"""Conbus client operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import (
    connection_command,
    handle_service_errors,
)
from xp.services.conbus.conbus_discover_service import (
    ConbusDiscoverError,
    ConbusDiscoverService,
)


@conbus.command("discover")
@connection_command()
@handle_service_errors(ConbusDiscoverError)
def send_discover_telegram() -> None:
    """
    Send discover telegram to Conbus server.

    Examples:

    \b
        xp conbus discover
    """
    service = ConbusDiscoverService()

    # Send telegram
    with service:
        response = service.send_discover_telegram()

    click.echo(json.dumps(response.to_dict(), indent=2))
