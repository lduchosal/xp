"""Version information operations CLI commands."""

import click
import json

from ...services.telegram_version_service import VersionService, VersionParsingError
from ..utils.decorators import handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from .telegram import telegram


@telegram.command("version")
@click.argument("serial_number", type=SERIAL)
@handle_service_errors(VersionParsingError)
def generate_version_request(serial_number: str) -> None:
    """
    Generate a telegram to request version information from a device.

    Examples:

    \b
        xp telegram version 0012345011
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
