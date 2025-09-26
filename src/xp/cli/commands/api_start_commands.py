"""API server start command."""

import sys

import click
import uvicorn

from .api import api


@api.command("start")
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to (default: 127.0.0.1)",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind the server to (default: 8000)",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    default=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--workers",
    default=1,
    type=int,
    help="Number of worker processes (default: 1)",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug", "trace"]),
    help="Log level (default: info)",
    show_default=True,
)
@click.option(
    "--access-log/--no-access-log",
    default=True,
    help="Enable/disable access log (default: enabled)",
)
def start_api_server(
    host: str, port: int, reload: bool, workers: int, log_level: str, access_log: bool
) -> None:
    """
    Start the FastAPI server.

    This command starts the XP Protocol FastAPI server using uvicorn.
    The server provides REST API endpoints for Conbus operations.

    Examples:

    \b
        # Start server on default host and port
        xp api start

    \b
        # Start server on specific host and port
        xp api start --host 0.0.0.0 --port 8080

    \b
        # Start development server with auto-reload
        xp api start --reload

    \b
        # Start production server with multiple workers
        xp api start --host 0.0.0.0 --workers 4 --no-access-log
    """

    # Validate workers and reload options
    if reload and workers > 1:
        click.echo(
            click.style(
                "Warning: Auto-reload is enabled. Setting workers to 1.",
                fg="yellow",
            )
        )
        workers = 1

    click.echo("Starting XP Protocol API server...")
    click.echo(f"Server will be available at: https://{host}:{port}")
    click.echo(f"API documentation at: https://{host}:{port}/docs")
    click.echo(f"Health check at: https://{host}:{port}/health")

    if reload:
        click.echo(click.style("Development mode: Auto-reload enabled", fg="green"))

    try:
        uvicorn.run(
            "xp.api.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level=log_level,
            access_log=access_log,
        )
    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(
            click.style(f"Error starting server: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)
