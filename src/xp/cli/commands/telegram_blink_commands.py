"""Blink operations CLI commands."""

import click
import json

from ...services.blink_service import BlinkService, BlinkError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from .telegram import blink

@blink.command("on")
@click.argument("serial_number", type=SERIAL)

@handle_service_errors(BlinkError)
def blink_on(serial_number: str):
    """
    Generate a telegram to start blinking module LED.

    Examples:

    \b
        xp blink on 0020044964
        xp blink on 0020044964
    """
    service = BlinkService()
    formatter = OutputFormatter(True)

    try:
        telegram = service.generate_blink_telegram(serial_number)

        output = {
            "success": True,
            "telegram": telegram,
            "serial_number": serial_number,
            "operation": "blink_on",
        }
        click.echo(json.dumps(output, indent=2))

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(e, "blink telegram generation", {"serial_number": serial_number})


@blink.command("off")
@click.argument("serial_number", type=SERIAL)

@handle_service_errors(BlinkError)
def blink_off(serial_number: str):
    """
    Generate a telegram to stop blinking module LED.

    Examples:

    \b
        xp blink off 0020030837
    """
    service = BlinkService()
    formatter = OutputFormatter(True)

    try:
        telegram = service.generate_unblink_telegram(serial_number)

        output = {
            "success": True,
            "telegram": telegram,
            "serial_number": serial_number,
            "operation": "blink_off",
        }
        click.echo(json.dumps(output, indent=2))

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(e, "unblink telegram generation", {"serial_number": serial_number})
