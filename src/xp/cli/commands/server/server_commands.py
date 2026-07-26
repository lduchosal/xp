# Copyright (c) 2025 ldvchosal
"""Conbus emulator server operations CLI commands."""

import json
import signal
from typing import Any

import click
from click import Context
from click_help_colors import HelpColorsGroup

from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import ServerErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.cli.utils.pid_file import remove_pid_file, write_pid_file
from xp.services.server.server_service import ServerError, ServerService


class ServerState:
    """Holds the process-wide server instance used by the CLI commands."""

    instance: ServerService | None = None


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def server() -> None:
    """Perform Conbus emulator server operations."""


@server.command("start")
@click.option(
    "--port", "-p", default=10001, type=int, help="Port to listen on (default: 10001)"
)
@click.option("--config", "-c", default="server.yml", help="Configuration file path")
@click.pass_context
@handle_service_errors(ServerError)
def start_server(ctx: Context, port: int, config: str) -> None:
    r"""Start the Conbus emulator server.

    Args:
        ctx: Click context object.
        port: Port to listen on.
        config: Configuration file path.

    Examples:
        \b
        xp server start
        xp server start --port 1001 --config my_config.yml

    Raises:
        SystemExit: If server is already running.

    """
    pid_file: str = ctx.obj.get("pid_file") or "server.pid"

    def signal_handler(_signum: int, _frame: object) -> None:
        """Handle SIGINT/SIGTERM signals by stopping the server.

        Args:
            _signum: Signal number received.
            _frame: Current stack frame.

        """
        if ServerState.instance and ServerState.instance.is_running:
            ServerState.instance.stop_server()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    write_pid_file(pid_file)

    try:
        # Check if server is already running
        if ServerState.instance and ServerState.instance.is_running:
            error_response = {
                "success": False,
                "error": "Server is already running",
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)

        # Get dependencies from container
        service: ServerService = (
            ctx.obj.get("container").get_container().resolve(ServerService)
        )
        ServerState.instance = service

        status = service.get_server_status()
        click.echo(json.dumps(status, indent=2))

        # This will block until server is stopped
        service.start_server()

        shutdown_response = {"success": True, "message": "Server shutdown"}
        click.echo(json.dumps(shutdown_response, indent=2))

    except ServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, port, config)
    finally:
        remove_pid_file(pid_file)


@server.command("stop")
@handle_service_errors(ServerError)
def stop_server() -> None:
    r"""Stop the running Conbus emulator server.

    Examples:
        \b
        xp server stop

    """
    try:
        if ServerState.instance is None or not ServerState.instance.is_running:
            ServerErrorHandler.handle_server_not_running_error()

        # Stop the server
        if ServerState.instance is not None:
            ServerState.instance.stop_server()

        response = {"success": True, "message": "Server stopped successfully"}
        click.echo(json.dumps(response, indent=2))

    except ServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, 0, "")


@server.command("status")
@handle_service_errors(Exception)
def server_status() -> None:
    r"""Get status of the Conbus emulator server.

    Examples:
        \b
        xp server status

    Raises:
        SystemExit: If status cannot be retrieved.

    """
    formatter = OutputFormatter(json_output=True)

    try:
        status: dict[str, Any]
        if ServerState.instance is None:
            status = {
                "running": False,
                "port": None,
                "devices_configured": 0,
                "device_list": [],
            }
        else:
            status = ServerState.instance.get_server_status()

        click.echo(json.dumps(status, indent=2))

    except Exception as e:
        error_response = formatter.error_response(str(e))
        click.echo(error_response)
        raise SystemExit(1) from e
