"""Conbus reverse proxy operations CLI commands."""

import click
import json
import signal
import sys

from ...services.conbus_reverse_proxy_service import (
    ConbusReverseProxyService,
    ConbusReverseProxyError,
)
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


# Global proxy instance
_proxy_instance = None


@click.group(name="rp")
def reverse_proxy():
    """Conbus reverse proxy operations"""
    pass


@reverse_proxy.command("start")
@click.option(
    "--port", "-p", default=10001, type=int, help="Port to listen on (default: 10001)"
)
@click.option("--config", "-c", default="rp.yml", help="Configuration file path")
@json_output_option
@handle_service_errors(ConbusReverseProxyError)
def start_proxy(port: int, config: str, json_output: bool):
    """
    Start the Conbus reverse proxy server.

    The proxy listens on the specified port and forwards all telegrams
    to the target server configured in cli.yml. All traffic is monitored
    and printed with timestamps.

    Example: xp rp start
    Example: xp rp start --port 10002 --config my_cli.yml
    """
    global _proxy_instance

    try:
        # Check if proxy is already running
        if _proxy_instance and _proxy_instance.is_running:
            if json_output:
                error_response = {
                    "success": False,
                    "error": "Reverse proxy is already running",
                }
                click.echo(json.dumps(error_response, indent=2))
                raise SystemExit(1)
            else:
                click.echo("Error: Reverse proxy is already running", err=True)
                raise click.ClickException("Reverse proxy already running")

        # Create proxy instance
        _proxy_instance = ConbusReverseProxyService(
            config_path=config, listen_port=port
        )

        # Handle graceful shutdown on SIGINT
        def signal_handler(signum, frame):
            if _proxy_instance and _proxy_instance.is_running:
                print(
                    f"\n{_proxy_instance._timestamp()} [SHUTDOWN] Received interrupt signal"
                )
                _proxy_instance.stop_proxy()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Start proxy (this will block)
        if json_output:
            result = _proxy_instance.start_proxy()
            click.echo(json.dumps(result.to_dict(), indent=2))
            if result.success:
                _proxy_instance.run_blocking()
        else:
            _proxy_instance.run_blocking()

    except ConbusReverseProxyError as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "reverse proxy startup", {"port": port, "config": config}
        )
    except KeyboardInterrupt:
        if json_output:
            shutdown_response = {
                "success": True,
                "message": "Reverse proxy shutdown by user",
            }
            click.echo(json.dumps(shutdown_response, indent=2))
        else:
            click.echo("\nReverse proxy shutdown by user")


@reverse_proxy.command("stop")
@json_output_option
@handle_service_errors(ConbusReverseProxyError)
def stop_proxy(json_output: bool):
    """
    Stop the running Conbus reverse proxy server.

    Example: xp rp stop
    """
    global _proxy_instance

    try:
        if _proxy_instance is None or not _proxy_instance.is_running:
            if json_output:
                error_response = {
                    "success": False,
                    "error": "Reverse proxy is not running",
                }
                click.echo(json.dumps(error_response, indent=2))
                raise SystemExit(1)
            else:
                click.echo("Error: Reverse proxy is not running", err=True)
                raise click.ClickException("Reverse proxy not running")

        # Stop the proxy
        result = _proxy_instance.stop_proxy()

        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            if result.success:
                click.echo("Reverse proxy stopped successfully")
            else:
                click.echo(f"Error stopping reverse proxy: {result.error}")

    except ConbusReverseProxyError as e:
        CLIErrorHandler.handle_service_error(e, json_output, "reverse proxy stop")


@reverse_proxy.command("status")
@json_output_option
@handle_service_errors(Exception)
def proxy_status(json_output: bool):
    """
    Get status of the Conbus reverse proxy server.

    Shows current running state, listen port, target server,
    and active connection details.

    Example: xp rp status
    """
    global _proxy_instance
    formatter = OutputFormatter(json_output)

    try:
        if _proxy_instance is None:
            status_data = {
                "running": False,
                "listen_port": None,
                "target_ip": None,
                "target_port": None,
                "active_connections": 0,
                "connections": {},
            }
        else:
            result = _proxy_instance.get_status()
            status_data = result.data if result.success else {}

        if json_output:
            click.echo(json.dumps(status_data, indent=2))
        else:
            if status_data.get("running", False):
                click.echo("✓ Reverse proxy is running")
                click.echo(f"  Listen port: {status_data.get('listen_port')}")
                click.echo(
                    f"  Target server: {status_data.get('target_ip')}:{status_data.get('target_port')}"
                )
                click.echo(
                    f"  Active connections: {status_data.get('active_connections', 0)}"
                )

                # Show connection details if any
                connections = status_data.get("connections", {})
                if connections:
                    click.echo("  Connection details:")
                    for conn_id, conn_info in connections.items():
                        client_addr = conn_info.get("client_address", "unknown")
                        connected_at = conn_info.get("connected_at", "unknown")
                        bytes_relayed = conn_info.get("bytes_relayed", 0)
                        click.echo(
                            f"    {conn_id}: {client_addr} (connected: {connected_at}, {bytes_relayed} bytes)"
                        )
            else:
                click.echo("✗ Reverse proxy is not running")

    except Exception as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "reverse proxy status check"
        )
