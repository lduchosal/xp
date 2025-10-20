"""Device discover operations CLI commands."""

import json

import click

from xp.cli.commands.telegram.telegram import telegram
from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.services.telegram.telegram_discover_service import (
    DiscoverError,
    TelegramDiscoverService,
)


@telegram.command("discover")
@handle_service_errors(DiscoverError)
def generate_discover() -> None:
    r"""Generate a discover telegram for device enumeration.

    Examples:
        \b
        xp telegram discover
    """
    service = TelegramDiscoverService()
    OutputFormatter(True)

    try:
        discover = service.generate_discover_telegram()

        output = {
            "success": True,
            "telegram": discover,
            "operation": "discover_broadcast",
            "broadcast_address": "0000000000",
        }
        click.echo(json.dumps(output, indent=2))

    except DiscoverError as e:
        CLIErrorHandler.handle_service_error(e, "discover telegram generation")
