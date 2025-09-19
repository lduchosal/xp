"""Device discovery operations CLI commands."""

import json

import click

from .telegram import telegram
from ..utils.decorators import handle_service_errors
from ..utils.error_handlers import CLIErrorHandler
from ..utils.formatters import OutputFormatter
from ...services.telegram_discovery_service import TelegramDiscoveryService, DiscoveryError


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
        discovery = service.generate_discovery_telegram()

        output = {
            "success": True,
            "telegram": discovery,
            "operation": "discovery_broadcast",
            "broadcast_address": "0000000000",
        }
        click.echo(json.dumps(output, indent=2))

    except DiscoveryError as e:
        CLIErrorHandler.handle_service_error(e, "discovery telegram generation")
