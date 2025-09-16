import json

import click

from xp.cli.utils.decorators import json_output_option, handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.services.conbus_client_send_service import ConbusClientSendService


@click.group()
def conbus():
    """Conbus client operations for sending telegrams to remote servers"""
    pass

@conbus.command("config")
@json_output_option
@handle_service_errors(Exception)
def show_config(json_output: bool):
    """
    Display current Conbus client configuration.

    Example: xp conbus config
    """
    service = ConbusClientSendService()
    formatter = OutputFormatter(json_output)

    try:
        config = service.get_config()

        if json_output:
            click.echo(json.dumps(config.to_dict(), indent=2))
        else:
            click.echo(f"  ip: {config.ip}")
            click.echo(f"  port: {config.port}")
            click.echo(f"  timeout: {config.timeout} seconds")

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, json_output, "configuration retrieval")

