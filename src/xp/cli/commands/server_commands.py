"""Conbus emulator server operations CLI commands."""

import click
import json

from ...services.conbus_server_service import ConbusServerService, ConbusServerError
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import ServerErrorHandler


# Global server instance
_server_instance = None


@click.group()
def server():
    """
    Conbus emulator server operations
    """
    pass


@server.command("start")
@click.option(
    "--port", "-p", default=10001, type=int, help="Port to listen on (default: 10001)"
)
@click.option("--config", "-c", default="config.yml", help="Configuration file path")

@handle_service_errors(ConbusServerError)
def start_server(port: int, config: str):
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
        _server_instance = ConbusServerService(config_path=config, port=port)

        status = _server_instance.get_server_status()
        click.echo(json.dumps(status, indent=2))

        # This will block until server is stopped
        _server_instance.start_server()

    except ConbusServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, True, port, config)
    except KeyboardInterrupt:
        shutdown_response = {"success": True, "message": "Server shutdown by user"}
        click.echo(json.dumps(shutdown_response, indent=2))


@server.command("stop")

@handle_service_errors(ConbusServerError)
def stop_server():
    """
    Stop the running Conbus emulator server.

    Examples:

    \b
        xp server stop
    """
    global _server_instance

    try:
        if _server_instance is None or not _server_instance.is_running:
            ServerErrorHandler.handle_server_not_running_error(True)

        # Stop the server
        _server_instance.stop_server()

        response = {"success": True, "message": "Server stopped successfully"}
        click.echo(json.dumps(response, indent=2))

    except ConbusServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, True, 0, "")


@server.command("status")

@handle_service_errors(Exception)
def server_status():
    """
    Get status of the Conbus emulator server.

    Examples:

    \b
        xp server status
    """
    global _server_instance
    formatter = OutputFormatter(True)

    try:
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
