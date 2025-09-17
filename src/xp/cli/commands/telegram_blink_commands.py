"""Blink operations CLI commands."""

import click
import json

from ...services.blink_service import BlinkService, BlinkError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from .telegram import blink

@blink.command("on")
@click.argument("serial_number", type=SERIAL)
@json_output_option
@handle_service_errors(BlinkError)
def blink_on(serial_number: str, json_output: bool):
    """
    Generate a telegram to start blinking module LED.

    Examples:

    \b
        xp blink on 0020044964
        xp blink on 0020044964
    """
    service = BlinkService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_blink_telegram(serial_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "blink_on",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Blink LED Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "blink telegram generation",
            {"serial_number": serial_number},
        )


@blink.command("off")
@click.argument("serial_number", type=SERIAL)
@json_output_option
@handle_service_errors(BlinkError)
def blink_off(serial_number: str, json_output: bool):
    """
    Generate a telegram to stop blinking module LED.

    Examples:

    \b
        xp blink off 0020030837
    """
    service = BlinkService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_unblink_telegram(serial_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "blink_off",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Unblink LED Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "unblink telegram generation",
            {"serial_number": serial_number},
        )
