"""Link number operations CLI commands."""

import click
import json

from ...services.link_number_service import LinkNumberService, LinkNumberError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from .telegram import linknumber


@linknumber.command("write")
@click.argument("serial_number")
@click.argument("link_number", type=int)
@json_output_option
@handle_service_errors(LinkNumberError)
def generate_set_link_number(serial_number: str, link_number: int, json_output: bool):
    """
    Generate a telegram to set module link number.

    Examples:

    \b
        xp telegram linknumber write 0020044974 25
    """
    service = LinkNumberService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_set_link_number_telegram(serial_number, link_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "link_number": link_number,
                "operation": "set_link_number",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Set Link Number Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Link Number: {link_number}")
            click.echo(f"Telegram: {telegram}")

    except LinkNumberError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "link number telegram generation",
            {"serial_number": serial_number, "link_number": link_number},
        )


@linknumber.command("read")
@click.argument("serial_number")
@json_output_option
@handle_service_errors(LinkNumberError)
def generate_read_link_number(serial_number: str, json_output: bool):
    """
    Generate a telegram to read module link number.

    Examples:

    \b
        xp telegram linknumber read 0020044974
    """
    service = LinkNumberService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_read_link_number_telegram(serial_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "read_link_number",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Read Link Number Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")

    except LinkNumberError as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "read telegram generation", {"serial_number": serial_number}
        )

