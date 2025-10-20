"""Checksum calculation and validation CLI commands."""

import json

import click

from xp.cli.commands.telegram.telegram import checksum
from xp.cli.utils.decorators import handle_service_errors
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter
from xp.services.telegram.telegram_checksum_service import TelegramChecksumService


@checksum.command("calculate")
@click.argument("data")
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(["simple", "crc32"]),
    default="simple",
    help="Checksum algorithm to use",
)
@handle_service_errors(Exception)
def calculate_checksum(data: str, algorithm: str) -> None:
    r"""Calculate checksum for given data string.

    Args:
        data: Data string to calculate checksum for.
        algorithm: Checksum algorithm to use.

    Examples:
        \b
        xp checksum calculate "E14L00I02M"
        xp checksum calculate "E14L00I02M" --algorithm crc32

    Raises:
        SystemExit: If checksum calculation fails.
    """
    service = TelegramChecksumService()
    formatter = OutputFormatter(True)

    try:
        if algorithm == "simple":
            result = service.calculate_simple_checksum(data)
        else:  # crc32
            result = service.calculate_crc32_checksum(data)

        if not result.success:
            error_response = formatter.error_response(
                result.error or "Unknown error", {"input": data}
            )
            click.echo(error_response)
            raise SystemExit(1)

        click.echo(json.dumps(result.to_dict(), indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "checksum calculation", {"input": data})


@checksum.command("validate")
@click.argument("data")
@click.argument("expected_checksum")
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(["simple", "crc32"]),
    default="simple",
    help="Checksum algorithm to use",
)
@handle_service_errors(Exception)
def validate_checksum(data: str, expected_checksum: str, algorithm: str) -> None:
    r"""Validate data against expected checksum.

    Args:
        data: Data string to validate.
        expected_checksum: Expected checksum value.
        algorithm: Checksum algorithm to use.

    Examples:
        \b
        xp checksum validate "E14L00I02M" "AK"
        xp checksum validate "E14L00I02M" "ABCDABCD" --algorithm crc32

    Raises:
        SystemExit: If checksum validation fails.
    """
    service = TelegramChecksumService()
    formatter = OutputFormatter(True)

    try:
        if algorithm == "simple":
            result = service.validate_checksum(data, expected_checksum)
        else:  # crc32
            result = service.validate_crc32_checksum(data, expected_checksum)

        if not result.success:
            error_response = formatter.error_response(
                result.error or "Unknown error",
                {"input": data, "expected_checksum": expected_checksum},
            )
            click.echo(error_response)
            raise SystemExit(1)

        click.echo(json.dumps(result.to_dict(), indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(
            e,
            "checksum validation",
            {"input": data, "expected_checksum": expected_checksum},
        )
