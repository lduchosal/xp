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
    r"""Send discover telegram to Conbus server.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp conbus discover
    """

    def on_finish(discovered_devices: ConbusDiscoverResponse) -> None:
        """Handle successful completion of device discovery.

        Args:
            discovered_devices: Discover response with all found devices.
        """
        click.echo(json.dumps(discovered_devices.to_dict(), indent=2))

    def progress(_serial_number: str) -> None:
        """Handle progress updates during device discovery.

        Args:
            _serial_number: Serial number of discovered device (unused).
        """
        # click.echo(f"Discovered : {serial_number}")
        pass

    service: ConbusDiscoverService = (
        ctx.obj.get("container").get_container().resolve(ConbusDiscoverService)
    )
    with service:
        service.start(progress, on_finish, 0.5)
