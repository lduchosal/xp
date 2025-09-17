"""Version information operations CLI commands."""

import click
import json

from ...services.version_service import VersionService, VersionParsingError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from .telegram import telegram

@telegram.command("version")
@click.argument("serial_number")
@json_output_option
@handle_service_errors(VersionParsingError)
def generate_version_request(serial_number: str, json_output: bool):
    """
    Generate a telegram to request version information from a device.

    Examples:

    \b
        xp telegram version 0020030837
    """
    service = VersionService()
    formatter = OutputFormatter(json_output)

    try:
        result = service.generate_version_request_telegram(serial_number)

        if not result.success:
            error_response = formatter.error_response(
                result.error, {"serial_number": serial_number}
            )
            click.echo(error_response)
            if json_output:
                raise SystemExit(1)
            else:
                raise click.ClickException("Version request generation failed")

        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo("Version Request Telegram:")
            click.echo(f"Serial: {result.data['serial_number']}")
            click.echo(f"Telegram: {result.data['telegram']}")
            click.echo(f"Function: {result.data['function_code']} (Read Data point)")
            click.echo(f"Data Point: {result.data['data_point_code']} (Version)")
            click.echo(f"Checksum: {result.data['checksum']}")

    except VersionParsingError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "version request generation",
            {"serial_number": serial_number},
        )

