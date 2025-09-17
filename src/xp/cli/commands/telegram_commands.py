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


@telegram.command("parse-event")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_event_telegram(
    telegram_string: str, validate_checksum: bool
):
    """
    Parse a single event telegram string.

    Examples:

    \b
        xp telegram parse-event "<E14L00I02MAK>"
    """
    service = TelegramService()
    formatter = TelegramFormatter(True)

    try:
        parsed = service.parse_event_telegram(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)

        output = parsed.to_dict()
        if validate_checksum:
            output["checksum_valid"] = checksum_valid
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, True, telegram_string)


@telegram.command("parse-system")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_system_telegram(
    telegram_string: str, validate_checksum: bool
):
    """
    Parse a system telegram string.

    Examples:

    \b
        xp telegram parse-system "<S0020012521F02D18FN>"
    """
    service = TelegramService()
    formatter = TelegramFormatter(True)

    try:
        parsed = service.parse_system_telegram(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)

        output = parsed.to_dict()
        if validate_checksum:
            output["checksum_valid"] = checksum_valid
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, True, telegram_string)


@telegram.command("parse-reply")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_reply_telegram(
    telegram_string: str, validate_checksum: bool
):
    """
    Parse a reply telegram string.

    Examples:

    \b
        xp telegram parse-reply "<R0020012521F02D18+26,0§CIL>"
    """
    service = TelegramService()
    formatter = TelegramFormatter(True)

    try:
        parsed = service.parse_reply_telegram(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)

        output = parsed.to_dict()
        if validate_checksum:
            output["checksum_valid"] = checksum_valid
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, True, telegram_string)


@telegram.command("parse-discover-request")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_discovery_request_telegram(
    telegram_string: str, validate_checksum: bool
):
    """
    Parse a discovery request telegram string.

    Examples:

    \b
        xp telegram parse-discover-request "<S0000000000F01D00FA>"
    """
    service = TelegramService()
    TelegramFormatter(True)

    try:
        parsed = service.parse_discovery_request(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_discovery_request_checksum(parsed)

        output = parsed.to_dict()
        if validate_checksum:
            output["checksum_valid"] = checksum_valid
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, True, telegram_string)


@telegram.command("parse-discover-response")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_discovery_response_telegram(
    telegram_string: str, validate_checksum: bool
):
    """
    Parse a discovery response telegram string.

    Examples:

    \b
        xp telegram parse-discover-response "<R0020030837F01DFM>"
    """
    service = TelegramService()
    TelegramFormatter(True)

    try:
        parsed = service.parse_discovery_response(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_discovery_response_checksum(parsed)

        output = parsed.to_dict()
        if validate_checksum:
            output["checksum_valid"] = checksum_valid
        click.echo(json.dumps(output, indent=2))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, True, telegram_string)


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


@telegram.command("parse-multiple")
@click.argument("data_stream")
@handle_service_errors(Exception)
def parse_multiple_telegrams(data_stream: str):
    """
    Parse multiple event telegrams from a data stream.

    Examples:

    \b
        xp telegram parse-multiple "Some data <E14L00I02MAK> more <E14L01I03BB1>"
    """
    service = TelegramService()
    TelegramFormatter(True)

    try:
        telegrams = service.parse_multiple_telegrams(data_stream)

        output = {
            "success": True,
            "count": len(telegrams),
            "telegrams": [t.to_dict() for t in telegrams],
        }
        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_parsing_error(
            e, True, data_stream, {"operation": "parse_multiple"}
        )


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
