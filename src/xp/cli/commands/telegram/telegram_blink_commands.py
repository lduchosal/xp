"""Blink operations CLI commands."""

import json

import click

from xp.cli.commands.telegram.telegram import blink
from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.cli.utils.serial_number_type import SERIAL
from xp.services.telegram.telegram_blink_service import BlinkError, TelegramBlinkService


@blink.command("on")
@click.argument("serial_number", type=SERIAL)
@handle_service_errors(BlinkError)
def blink_on(serial_number: str) -> None:
    r"""Generate a telegram to start blinking module LED.

    Args:
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp blink on 0012345008
        xp blink on 0012345008
    """
    service = TelegramBlinkService()
    OutputFormatter(True)

    try:
        telegram = service.generate_blink_telegram(serial_number, "on")

        output = {
            "success": True,
            "telegram": telegram,
            "serial_number": serial_number,
            "operation": "blink_on",
        }
        click.echo(json.dumps(output, indent=2))

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(
            e, "blink telegram generation", {"serial_number": serial_number}
        )


@blink.command("off")
@click.argument("serial_number", type=SERIAL)
@handle_service_errors(BlinkError)
def blink_off(serial_number: str) -> None:
    r"""Generate a telegram to stop blinking module LED.

    Args:
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp blink off 0012345011
    """
    service = TelegramBlinkService()
    OutputFormatter(True)

    try:
        telegram = service.generate_blink_telegram(serial_number, "off")

        output = {
            "success": True,
            "telegram": telegram,
            "serial_number": serial_number,
            "operation": "blink_off",
        }
        click.echo(json.dumps(output, indent=2))

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(
            e, "unblink telegram generation", {"serial_number": serial_number}
        )
