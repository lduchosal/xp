"""Conbus emulator server operations CLI commands."""

from typing import Optional, Dict, Any

import click
import json
from click_help_colors import HelpColorsGroup

from ...services.server_service import ServerService, ServerError
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import ServerErrorHandler


# Global server instance
_server_instance: Optional[ServerService] = None


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def server() -> None:
    """
    Conbus emulator server operations
    """
    pass


@server.command("start")
@click.option(
    "--port", "-p", default=10001, type=int, help="Port to listen on (default: 10001)"
)
@click.option("--config", "-c", default="server.yml", help="Configuration file path")
@handle_service_errors(ServerError)
def start_server(port: int, config: str) -> None:
    """
    Start the Conbus emulator server.

    Examples:

    \b
        xp server start
        xp server start --port 1001 --config my_config.yml
    """
    global _server_instance

    try:
        # Check if server is already running
        if _server_instance and _server_instance.is_running:
            error_response = {
                "success": False,
                "error": "Server is already running",
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)

        # Create and start server
        _server_instance = ServerService(config_path=config, port=port)

        status = _server_instance.get_server_status()
        click.echo(json.dumps(status, indent=2))

        # This will block until server is stopped
        _server_instance.start_server()

    except ServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, port, config)
    except KeyboardInterrupt:
        shutdown_response = {"success": True, "message": "Server shutdown by user"}
        click.echo(json.dumps(shutdown_response, indent=2))


@server.command("stop")
@handle_service_errors(ServerError)
def stop_server() -> None:
    """
    Stop the running Conbus emulator server.

    Examples:

    \b
        xp server stop
    """
    global _server_instance

    try:
        if _server_instance is None or not _server_instance.is_running:
            ServerErrorHandler.handle_server_not_running_error()

        # Stop the server
        if _server_instance is not None:
            _server_instance.stop_server()

        response = {"success": True, "message": "Server stopped successfully"}
        click.echo(json.dumps(response, indent=2))

    except ServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, 0, "")


@server.command("status")
@handle_service_errors(Exception)
def server_status() -> None:
    """
    Get status of the Conbus emulator server.

    Examples:

    \b
        xp server status
    """
    global _server_instance
    formatter = OutputFormatter(True)

    try:
        status: Dict[str, Any]
        if _server_instance is None:
            status = {
                "running": False,
                "port": None,
                "devices_configured": 0,
                "device_list": [],
            }
        else:
            status = _server_instance.get_server_status()

        click.echo(json.dumps(status, indent=2))

    except Exception as e:
        error_response = formatter.error_response(str(e))
        click.echo(error_response)
        raise SystemExit(1)
