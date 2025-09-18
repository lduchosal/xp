"""Device discovery operations CLI commands."""

import click
import json

from . import telegram
from ...services.telegram_discovery_service import TelegramDiscoveryService, DiscoveryError
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from .telegram import telegram

@telegram.command("discover")
@handle_service_errors(DiscoveryError)
def generate_discovery():
    """
    Generate a discovery telegram for device enumeration.

    Examples:

    \b
        xp telegram discover
    """
    service = TelegramDiscoveryService()
    OutputFormatter(True)

    try:
        telegram = service.generate_discovery_telegram()

        output = {
            "success": True,
            "telegram": telegram,
            "operation": "discovery_broadcast",
            "broadcast_address": "0000000000",
        }
        click.echo(json.dumps(output, indent=2))

    except DiscoveryError as e:
        CLIErrorHandler.handle_service_error(e, "discovery telegram generation")
