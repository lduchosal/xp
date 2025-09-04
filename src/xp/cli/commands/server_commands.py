"""Conbus emulator server operations CLI commands."""
import click
import json

from ...services.conbus_server_service import ConbusServerService, ConbusServerError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import ServerErrorHandler


# Global server instance
_server_instance = None


@click.group()
def server():
    """Conbus emulator server operations"""
    pass


@server.command("start")
@click.option('--port', '-p', default=10001, type=int, help='Port to listen on (default: 10001)')
@click.option('--config', '-c', default="config.yml", help='Configuration file path')
@json_output_option
@handle_service_errors(ConbusServerError)
def start_server(port: int, config: str, json_output: bool):
    """
    Start the Conbus emulator server.
    
    Example: xp server start
    Example: xp server start --port 1001 --config my_config.yml
    """
    global _server_instance
    
    try:
        # Check if server is already running
        if _server_instance and _server_instance.is_running:
            if json_output:
                error_response = {
                    "success": False,
                    "error": "Server is already running"
                }
                click.echo(json.dumps(error_response, indent=2))
                raise SystemExit(1)
            else:
                click.echo("Error: Server is already running", err=True)
                raise click.ClickException("Server already running")
        
        # Create and start server
        _server_instance = ConbusServerService(config_path=config, port=port)
        
        if json_output:
            status = _server_instance.get_server_status()
            click.echo(json.dumps(status, indent=2))
        else:
            click.echo(f"Starting Conbus emulator server...")
            click.echo(f"Port: {port}")
            click.echo(f"Config: {config}")
            
        # This will block until server is stopped
        _server_instance.start_server()
        
    except ConbusServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, json_output, port, config)
    except KeyboardInterrupt:
        if json_output:
            shutdown_response = {
                "success": True,
                "message": "Server shutdown by user"
            }
            click.echo(json.dumps(shutdown_response, indent=2))
        else:
            click.echo(f"\nServer shutdown by user")


@server.command("stop")
@json_output_option
@handle_service_errors(ConbusServerError)
def stop_server(json_output: bool):
    """
    Stop the running Conbus emulator server.
    
    Example: xp server stop
    """
    global _server_instance
    
    try:
        if _server_instance is None or not _server_instance.is_running:
            ServerErrorHandler.handle_server_not_running_error(json_output)
        
        # Stop the server
        _server_instance.stop_server()
        
        if json_output:
            response = {
                "success": True,
                "message": "Server stopped successfully"
            }
            click.echo(json.dumps(response, indent=2))
        else:
            click.echo("Server stopped successfully")
            
    except ConbusServerError as e:
        ServerErrorHandler.handle_server_startup_error(e, json_output, 0, "")


@server.command("status")
@json_output_option
@handle_service_errors(Exception)
def server_status(json_output: bool):
    """
    Get status of the Conbus emulator server.
    
    Example: xp server status
    """
    global _server_instance
    formatter = OutputFormatter(json_output)
    
    try:
        if _server_instance is None:
            status = {
                "running": False,
                "port": None,
                "devices_configured": 0,
                "device_list": []
            }
        else:
            status = _server_instance.get_server_status()
        
        if json_output:
            click.echo(json.dumps(status, indent=2))
        else:
            if status["running"]:
                click.echo("✓ Server is running")
                click.echo(f"  Port: {status['port']}")
                click.echo(f"  Devices configured: {status['devices_configured']}")
                if status['device_list']:
                    click.echo(f"  Device list: {', '.join(status['device_list'])}")
            else:
                click.echo("✗ Server is not running")
                
    except Exception as e:
        error_response = formatter.error_response(str(e))
        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo(f"Error getting server status: {e}", err=True)
            raise click.ClickException("Status check failed")