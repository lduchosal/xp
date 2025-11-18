"""Conbus client operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.models import ConbusDiscoverResponse
from xp.models.conbus.conbus_discover import DiscoveredDevice
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
        service.stop_reactor()

    def on_device_discovered(discovered_device: DiscoveredDevice) -> None:
        """Handle discovery of sa single module.

        Args:
            discovered_device: Discover device.
        """
        click.echo(json.dumps(discovered_device, indent=2))

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
        service.on_progress.connect(progress)
        service.on_device_discovered.connect(on_device_discovered)
        service.on_finish.connect(on_finish)
        service.set_timeout(5)
        service.start_reactor()
