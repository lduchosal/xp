"""API server start command."""

import sys

import click

from .homekit import homekit
from ...services.homekit_service import HomekitService


@homekit.command("start")
def homekit_start() -> None:
    """
    Start the HomeKit server.

    This command starts the XP Protocol HomeKit server using HAP-python.
    The server provides HomeKit endpoints for Conbus operations.

    Examples:

    \b
        # Start server on default host and port
        xp homekit start

    """
    # Validate workers and reload options
    click.echo("Starting XP Protocol HomeKit server...")

    try:

        service = HomekitService()
        service.run()

    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(
            click.style(f"Error starting server: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)
