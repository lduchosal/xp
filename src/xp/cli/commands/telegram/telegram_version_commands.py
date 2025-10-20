"""Version information operations CLI commands."""

import json

import click

from xp.cli.commands.telegram.telegram import telegram
from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.cli.utils.serial_number_type import SERIAL
from xp.services.telegram.telegram_version_service import (
    VersionParsingError,
    VersionService,
)


@telegram.command("version")
@click.argument("serial_number", type=SERIAL)
@handle_service_errors(VersionParsingError)
def generate_version_request(serial_number: str) -> None:
    r"""Generate a telegram to request version information from a device.

    Args:
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp telegram version 0012345011

    Raises:
        SystemExit: If request cannot be generated.
    """
    service = VersionService()
    formatter = OutputFormatter(True)

    try:
        result = service.generate_version_request_telegram(serial_number)

        if not result.success:
            error_response = formatter.error_response(
                result.error or "Unknown error", {"serial_number": serial_number}
            )
            click.echo(error_response)
            raise SystemExit(1)

        click.echo(json.dumps(result.to_dict(), indent=2))

    except VersionParsingError as e:
        CLIErrorHandler.handle_service_error(
            e, "version request generation", {"serial_number": serial_number}
        )
