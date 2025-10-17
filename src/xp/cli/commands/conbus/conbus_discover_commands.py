"""Conbus client operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.models import ConbusDiscoverResponse
from xp.services.conbus.conbus_discover_service import (
    ConbusDiscoverService,
)


@conbus.command("discover")
@click.pass_context
@connection_command()
def send_discover_telegram(ctx: click.Context) -> None:
    """
    Send discover telegram to Conbus server.

    Examples:

    \b
        xp conbus discover
    """

    def finish(discovered_devices: ConbusDiscoverResponse) -> None:
        click.echo(json.dumps(discovered_devices.to_dict(), indent=2))

    def progress(_serial_number: str) -> None:
        # click.echo(f"Discovered : {serial_number}")
        pass

    service = ctx.obj.get("container").get_container().resolve(ConbusDiscoverService)
    with service:
        service.start(progress, finish, 0.5)
