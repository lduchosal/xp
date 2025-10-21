"""API server start command."""

import sys

import click
from click import Context

from xp.cli.commands.homekit.homekit import homekit
from xp.services.homekit.homekit_service import HomeKitService


@homekit.command("start")
@click.pass_context
def homekit_start(ctx: Context) -> None:
    r"""Start the HomeKit server.

    This command starts the XP Protocol HomeKit server using HAP-python.
    The server provides HomeKit endpoints for Conbus operations.

    Args:
        ctx: Click context object.

    Examples:
        \b
        # Start server on default host and port
        xp homekit start
    """
    click.echo("Starting XP Protocol HomeKit server...")

    try:
        service: HomeKitService = (
            ctx.obj.get("container").get_container().resolve(HomeKitService)
        )
        service.start()  # Blocking call - reactor.run() never returns

    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(
            click.style(f"Error starting server: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)
