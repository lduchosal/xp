import json

import click

from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from .conbus import conbus
from ...services.conbus_service import ConbusService


@conbus.command("config")
@handle_service_errors(Exception)
def show_config() -> None:
    """
    Display current Conbus client configuration.

    Examples:

    \b
        xp conbus config
    """
    service = ConbusService()
    OutputFormatter(True)

    try:
        config = service.get_config()
        click.echo(json.dumps(config.to_dict(), indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "configuration retrieval")
