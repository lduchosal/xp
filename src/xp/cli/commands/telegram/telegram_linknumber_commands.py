"""Link number operations CLI commands."""

import json

import click

from xp.cli.commands.telegram.telegram import linknumber
from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.cli.utils.serial_number_type import SERIAL
from xp.services.telegram.telegram_link_number_service import (
    LinkNumberError,
    LinkNumberService,
)


@linknumber.command("write")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=int)
@handle_service_errors(LinkNumberError)
def generate_set_link_number(serial_number: str, link_number: int) -> None:
    r"""Generate a telegram to set module link number.

    Args:
        serial_number: 10-digit module serial number.
        link_number: Link number to set.

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
    r"""Generate a telegram to read module link number.

    Args:
        serial_number: 10-digit module serial number.

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
