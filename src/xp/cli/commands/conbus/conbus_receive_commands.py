"""Conbus receive telegrams CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.models.conbus.conbus_receive import ConbusReceiveResponse
from xp.services.conbus.conbus_receive_service import (
    ConbusReceiveService,
)


@conbus.command("receive")
@click.argument("timeout", type=click.FLOAT, default=2.0)
@connection_command()
@click.pass_context
def receive_telegrams(ctx: Context, timeout: float) -> None:
    r"""Receive waiting event telegrams from Conbus server.

    Connects to the Conbus server and receives any waiting event telegrams
    without sending any data first. Useful for collecting pending notifications
    or events from the server.

    Args:
        ctx: Click context object.
        timeout: Timeout in seconds for receiving telegrams (default: 2.0).

    Examples:
        \b
        xp conbus receive
        xp conbus receive 5.0
    """

    def on_finish(response_received: ConbusReceiveResponse) -> None:
        """Handle successful completion of telegram receive operation.

        Args:
            response_received: Receive response object with telegrams.
        """
        click.echo(json.dumps(response_received.to_dict(), indent=2))
        service.stop_reactor()

    def on_progress(telegram_received: str) -> None:
        """Handle progress updates during telegram receive operation.

        Args:
            telegram_received: Received telegram string.
        """
        click.echo(telegram_received)

    service: ConbusReceiveService = (
        ctx.obj.get("container").get_container().resolve(ConbusReceiveService)
    )
    with service:
        service.on_progress.connect(on_progress)
        service.on_finish.connect(on_finish)
        service.set_timeout(timeout)
        service.start_reactor()
