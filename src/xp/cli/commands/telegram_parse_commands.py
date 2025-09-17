"""Telegram-related CLI commands."""

import click
import json

from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import (
    telegram_parser_command,
    handle_service_errors,
)
from ..utils.formatters import TelegramFormatter
from ..utils.error_handlers import CLIErrorHandler
from .telegram import telegram


@telegram.command("parse")
@click.argument("telegram_string")
@handle_service_errors(TelegramParsingError)
def parse_any_telegram(telegram_string: str):
    """
    Auto-detect and parse any type of telegram (event, system, reply, or discovery).

    Examples:

    \b
        xp telegram parse "<E14L00I02MAK>"
        xp telegram parse "<S0020012521F02D18FN>"
        xp telegram parse "<R0020012521F02D18+26,0§CIL>"
        xp telegram parse "<S0000000000F01D00FA>"
        xp telegram parse "<R0020030837F01DFM>"
    """
    service = TelegramService()
    TelegramFormatter(True)

    try:
        parsed = service.parse_telegram(telegram_string)
        output = parsed.to_dict()
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, True, telegram_string)


@telegram.command("validate")
@click.argument("telegram_string")
@handle_service_errors(TelegramParsingError)
def validate_telegram(telegram_string: str):
    """
    Validate the format of an event telegram.

    Examples:

    \b
        xp telegram validate "<E14L00I02MAK>"
    """
    service = TelegramService()
    TelegramFormatter(True)

    try:
        parsed = service.parse_event_telegram(telegram_string)
        checksum_valid = service.validate_checksum(parsed)

        output = {
            "success": True,
            "valid_format": True,
            "valid_checksum": checksum_valid,
            "telegram": parsed.to_dict(),
        }
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_validation_error(e, True, telegram_string)
