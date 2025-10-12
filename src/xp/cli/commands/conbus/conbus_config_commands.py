import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.services.conbus.conbus_service import ConbusService


@conbus.command("config")
@click.pass_context
@handle_service_errors(Exception)
def show_config(ctx: Context) -> None:
    """
    Display current Conbus client configuration.

    Examples:

    \b
        xp conbus config
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusService)
    OutputFormatter(True)

    try:
        config = service.get_config()
        click.echo(json.dumps(config.conbus.model_dump(mode="json"), indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "configuration retrieval")
