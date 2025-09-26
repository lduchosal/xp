"""Link number operations CLI commands."""

import click
import json

from ...services.telegram_link_number_service import LinkNumberService, LinkNumberError
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from .telegram import linknumber


@linknumber.command("write")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=int)
@handle_service_errors(LinkNumberError)
def generate_set_link_number(serial_number: str, link_number: int) -> None:
    """
    Generate a telegram to set module link number.

    Examples:

    \b
        xp telegram linknumber write 0012345005 25
    """
    service = LinkNumberService()
    OutputFormatter(True)

    try:
        telegram = service.generate_set_link_number_telegram(serial_number, link_number)

        output = {
            "success": True,
            "telegram": telegram,
            "serial_number": serial_number,
            "link_number": link_number,
            "operation": "set_link_number",
        }
        click.echo(json.dumps(output, indent=2))

    except LinkNumberError as e:
        CLIErrorHandler.handle_service_error(
            e,
            "link number telegram generation",
            {"serial_number": serial_number, "link_number": link_number},
        )


@linknumber.command("read")
@click.argument("serial_number", type=SERIAL)
@handle_service_errors(LinkNumberError)
def generate_read_link_number(serial_number: str) -> None:
    """
    Generate a telegram to read module link number.

    Examples:

    \b
        xp telegram linknumber read 0012345005
    """
    service = LinkNumberService()
    OutputFormatter(True)

    try:
        telegram = service.generate_read_link_number_telegram(serial_number)

        output = {
            "success": True,
            "telegram": telegram,
            "serial_number": serial_number,
            "operation": "read_link_number",
        }
        click.echo(json.dumps(output, indent=2))

    except LinkNumberError as e:
        CLIErrorHandler.handle_service_error(
            e, "read telegram generation", {"serial_number": serial_number}
        )
