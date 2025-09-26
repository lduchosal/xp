"""Conbus reverse proxy operations CLI commands."""

import click
import json
import signal
import sys
from click_help_colors import HelpColorsGroup

from typing import Optional, Dict, Any
from types import FrameType

from ...services.reverse_proxy_service import (
    ReverseProxyService,
    ReverseProxyError,
)
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


# Global proxy instance
global_proxy_instance: Optional[ReverseProxyService] = None


@click.group(
    name="rp",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def reverse_proxy() -> None:
    """
    Conbus reverse proxy operations
    """
    pass


@reverse_proxy.command("start")
@click.option(
    "--port", "-p", default=10001, type=int, help="Port to listen on (default: 10001)"
)
@click.option("--config", "-c", default="rp.yml", help="Configuration file path")
@handle_service_errors(ReverseProxyError)
def start_proxy(port: int, config: str) -> None:
    """
    Start the Conbus reverse proxy server.

    The proxy listens on the specified port and forwards all telegrams
    to the target server configured in cli.yml. All traffic is monitored
    and printed with timestamps.

    Examples:

    \b
        xp rp start
        xp rp start --port 10002 --config my_cli.yml
    """
    global global_proxy_instance

    try:
        # Check if proxy is already running
        if global_proxy_instance and global_proxy_instance.is_running:
            error_response = {
                "success": False,
                "error": "Reverse proxy is already running",
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)

        # Create proxy instance
        global_proxy_instance = ReverseProxyService(
            config_path=config, listen_port=port
        )

        # Handle graceful shutdown on SIGINT
        def signal_handler(signum: int, frame: Optional[FrameType]) -> None:
            if global_proxy_instance and global_proxy_instance.is_running:
                timestamp = global_proxy_instance.timestamp()
                print(f"\n{timestamp} [SHUTDOWN] Received interrupt signal ({signum})")
                print(f"\n{timestamp} [SHUTDOWN] Frame is ({frame})")
                global_proxy_instance.stop_proxy()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Start proxy (this will block)
        result = global_proxy_instance.start_proxy()
        click.echo(json.dumps(result.to_dict(), indent=2))
        if result.success:
            global_proxy_instance.run_blocking()

    except ReverseProxyError as e:
        CLIErrorHandler.handle_service_error(
            e, "reverse proxy startup", {"port": port, "config": config}
        )
    except KeyboardInterrupt:
        shutdown_response = {
            "success": True,
            "message": "Reverse proxy shutdown by user",
        }
        click.echo(json.dumps(shutdown_response, indent=2))


@reverse_proxy.command("stop")
@handle_service_errors(ReverseProxyError)
def stop_proxy() -> None:
    """
    Stop the running Conbus reverse proxy server.

    Examples:

    \b
        xp rp stop
    """
    global global_proxy_instance

    try:
        if global_proxy_instance is None or not global_proxy_instance.is_running:
            error_response = {
                "success": False,
                "error": "Reverse proxy is not running",
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)

        # Stop the proxy
        result = global_proxy_instance.stop_proxy()

        click.echo(json.dumps(result.to_dict(), indent=2))

    except ReverseProxyError as e:
        CLIErrorHandler.handle_service_error(e, "reverse proxy stop")


@reverse_proxy.command("status")
@handle_service_errors(Exception)
def proxy_status() -> None:
    """
    Get status of the Conbus reverse proxy server.

    Shows current running state, listen port, target server,
    and active connection details.

    Examples:

    \b
        xp rp status
    """
    global global_proxy_instance
    OutputFormatter(True)

    try:
        status_data: Dict[str, Any]
        if global_proxy_instance is None:
            status_data = {
                "running": False,
                "listen_port": None,
                "target_ip": None,
                "target_port": None,
                "active_connections": 0,
                "connections": {},
            }
        else:
            result = global_proxy_instance.get_status()
            status_data = result.data if result.success else {}

        click.echo(json.dumps(status_data, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "reverse proxy status check")
