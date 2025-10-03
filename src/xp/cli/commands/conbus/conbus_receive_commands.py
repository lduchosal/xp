"""Conbus receive telegrams CLI commands."""

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import (
    connection_command,
    handle_service_errors,
)
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.services.conbus.conbus_receive_service import (
    ConbusReceiveError,
    ConbusReceiveService,
)


@conbus.command("receive")
@click.argument("timeout", type=click.FLOAT, default=2.0)
@connection_command()
@handle_service_errors(ConbusReceiveError)
@click.pass_context
def receive_telegrams(ctx: Context, timeout: float) -> None:
    """
    Receive waiting event telegrams from Conbus server.

    Connects to the Conbus server and receives any waiting event telegrams
    without sending any data first. Useful for collecting pending notifications
    or events from the server.

    Arguments:
        :param timeout: Timeout in seconds for receiving telegrams (default: 2.0)

    Examples:

    \b
        xp conbus receive
        xp conbus receive 5.0
    """
    # Get service from container
    service = ctx.obj.get("container").get_container().resolve(ConbusReceiveService)

    try:
        with service:
            response = service.receive_telegrams(timeout=timeout)

        # Format output to match expected format from documentation
        if response.success and response.received_telegrams:
            for telegram in response.received_telegrams:
                click.echo(telegram)
        elif response.success:
            # No output if no telegrams received (silent success)
            pass
        else:
            click.echo(f"Error: {response.error}", err=True)

    except ConbusReceiveError as e:
        CLIErrorHandler.handle_service_error(e, "telegram receive", {})
