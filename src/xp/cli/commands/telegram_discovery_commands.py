"""Device discovery operations CLI commands."""

import click
import json

from ...services.discovery_service import DiscoveryService, DiscoveryError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter, ListFormatter
from ..utils.error_handlers import CLIErrorHandler
from .telegram import discovery

@discovery.command("generate")
@json_output_option
@handle_service_errors(DiscoveryError)
def generate_discovery(json_output: bool):
    """
    Generate a discovery telegram for device enumeration.

    Examples:

    \b
        xp telegram discovery generate
    """
    service = DiscoveryService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_discovery_telegram()

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "operation": "discovery_broadcast",
                "broadcast_address": "0000000000",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Discovery Broadcast Telegram:")
            click.echo("Broadcast Address: 0000000000")
            click.echo(f"Telegram: {telegram}")
            click.echo(
                "\nUse this telegram to enumerate all devices on the console bus."
            )

    except DiscoveryError as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "discovery telegram generation"
        )
