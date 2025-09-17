"""Telegram-related CLI commands."""

import click
import json

from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import (
    telegram_parser_command,
    json_output_option,
    handle_service_errors,
)
from ..utils.formatters import TelegramFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def telegram():
    """
    Event telegram operations
    """
    pass


@telegram.command("parse-event")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_event_telegram(
    telegram_string: str, json_output: bool, validate_checksum: bool
):
    """
    Parse a single event telegram string.

    Example:

    \b
        xp telegram parse-event "<E14L00I02MAK>"
    """
    service = TelegramService()
    formatter = TelegramFormatter(json_output)

    try:
        parsed = service.parse_event_telegram(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)

        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output["checksum_valid"] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            summary = service.format_event_telegram_summary(parsed)
            click.echo(
                formatter.format_validation_result(parsed, checksum_valid, summary)
            )

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)


@telegram.command("parse-system")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_system_telegram(
    telegram_string: str, json_output: bool, validate_checksum: bool
):
    """
    Parse a system telegram string.

    Example:

    \b
        xp telegram parse-system "<S0020012521F02D18FN>"
    """
    service = TelegramService()
    formatter = TelegramFormatter(json_output)

    try:
        parsed = service.parse_system_telegram(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)

        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output["checksum_valid"] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            summary = service.format_system_telegram_summary(parsed)
            click.echo(
                formatter.format_validation_result(parsed, checksum_valid, summary)
            )

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)


@telegram.command("parse-reply")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_reply_telegram(
    telegram_string: str, json_output: bool, validate_checksum: bool
):
    """
    Parse a reply telegram string.

    Example:

    \b
        xp telegram parse-reply "<R0020012521F02D18+26,0§CIL>"
    """
    service = TelegramService()
    formatter = TelegramFormatter(json_output)

    try:
        parsed = service.parse_reply_telegram(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)

        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output["checksum_valid"] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            summary = service.format_reply_telegram_summary(parsed)
            click.echo(
                formatter.format_validation_result(parsed, checksum_valid, summary)
            )

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)


@telegram.command("parse-discover-request")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_discovery_request_telegram(
    telegram_string: str, json_output: bool, validate_checksum: bool
):
    """
    Parse a discovery request telegram string.

    Example:

    \b
        xp telegram parse-discover-request "<S0000000000F01D00FA>"
    """
    service = TelegramService()
    TelegramFormatter(json_output)

    try:
        parsed = service.parse_discovery_request(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_discovery_request_checksum(parsed)

        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output["checksum_valid"] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            broadcast_info = (
                "Broadcast "
                if parsed.is_broadcast
                else f"From {parsed.source_address} "
            )
            lines = [
                f"Discovery Request: {broadcast_info}Command",
                f"Source: {parsed.source_address}",
                f"Command: {parsed.command}",
                f"Raw: {parsed.raw_telegram}",
                f"Timestamp: {parsed.timestamp}",
                f"Checksum: {parsed.checksum}",
            ]

            if validate_checksum:
                status = "✓ Valid" if checksum_valid else "✗ Invalid"
                lines.append(f"Checksum validation: {status}")

            click.echo("\n".join(lines))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)


@telegram.command("parse-discover-response")
@click.argument("telegram_string")
@telegram_parser_command()
def parse_discovery_response_telegram(
    telegram_string: str, json_output: bool, validate_checksum: bool
):
    """
    Parse a discovery response telegram string.

    Example:

    \b
        xp telegram parse-discover-response "<R0020030837F01DFM>"
    """
    service = TelegramService()
    TelegramFormatter(json_output)

    try:
        parsed = service.parse_discovery_response(telegram_string)

        # Validate checksum if requested
        checksum_valid = None
        if validate_checksum:
            checksum_valid = service.validate_discovery_response_checksum(parsed)

        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output["checksum_valid"] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            lines = [
                f"Discovery Response: Device {parsed.serial_number} Online",
                f"Serial: {parsed.serial_number}",
                f"Command: {parsed.full_command}",
                f"Raw: {parsed.raw_telegram}",
                f"Timestamp: {parsed.timestamp}",
                f"Checksum: {parsed.checksum}",
            ]

            if validate_checksum:
                status = "✓ Valid" if checksum_valid else "✗ Invalid"
                lines.append(f"Checksum validation: {status}")

            click.echo("\n".join(lines))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)


@telegram.command("parse")
@click.argument("telegram_string")
@json_output_option
@handle_service_errors(TelegramParsingError)
def parse_any_telegram(telegram_string: str, json_output: bool):
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
    TelegramFormatter(json_output)

    try:
        parsed = service.parse_telegram(telegram_string)

        if json_output:
            output = parsed.to_dict()
            click.echo(json.dumps(output, indent=2))
        else:
            # Format based on telegram type
            if hasattr(parsed, "event_type"):  # EventTelegram
                click.echo(service.format_event_telegram_summary(parsed))
            elif hasattr(parsed, "data_value"):  # ReplyTelegram
                click.echo(service.format_reply_telegram_summary(parsed))
            elif hasattr(parsed, "source_address"):  # DiscoveryRequest
                broadcast_info = (
                    "Broadcast "
                    if parsed.is_broadcast
                    else f"From {parsed.source_address} "
                )
                click.echo(f"Discovery Request: {broadcast_info}Command")
                click.echo(f"Raw: {parsed.raw_telegram}")
                click.echo(f"Timestamp: {parsed.timestamp}")
            elif hasattr(parsed, "device_id"):  # DiscoveryResponse
                click.echo(f"Discovery Response: Device {parsed.serial_number} Online")
                click.echo(f"Raw: {parsed.raw_telegram}")
                click.echo(f"Timestamp: {parsed.timestamp}")
            else:  # SystemTelegram
                click.echo(service.format_system_telegram_summary(parsed))

    except TelegramParsingError as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)


@telegram.command("parse-multiple")
@click.argument("data_stream")
@json_output_option
@handle_service_errors(Exception)
def parse_multiple_telegrams(data_stream: str, json_output: bool):
    """
    Parse multiple event telegrams from a data stream.

    Example:

    \b
        xp telegram parse-multiple "Some data <E14L00I02MAK> more <E14L01I03BB1>"
    """
    service = TelegramService()
    TelegramFormatter(json_output)

    try:
        telegrams = service.parse_multiple_telegrams(data_stream)

        if json_output:
            output = {
                "success": True,
                "count": len(telegrams),
                "telegrams": [t.to_dict() for t in telegrams],
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Found {len(telegrams)} telegrams:")
            click.echo("-" * 50)
            for i, telegram in enumerate(telegrams, 1):
                click.echo(f"{i}. {telegram}")

    except Exception as e:
        CLIErrorHandler.handle_parsing_error(
            e, json_output, data_stream, {"operation": "parse_multiple"}
        )


@telegram.command("validate")
@click.argument("telegram_string")
@json_output_option
@handle_service_errors(TelegramParsingError)
def validate_telegram(telegram_string: str, json_output: bool):
    """
    Validate the format of an event telegram.

    Example:

    \b
        xp telegram validate "<E14L00I02MAK>"
    """
    service = TelegramService()
    TelegramFormatter(json_output)

    try:
        parsed = service.parse_event_telegram(telegram_string)
        checksum_valid = service.validate_checksum(parsed)

        if json_output:
            output = {
                "success": True,
                "valid_format": True,
                "valid_checksum": checksum_valid,
                "telegram": parsed.to_dict(),
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("✓ Telegram format is valid")
            checksum_status = "✓ Valid" if checksum_valid else "✗ Invalid"
            click.echo(f"Checksum: {checksum_status}")
            click.echo(f"Parsed: {parsed}")

    except TelegramParsingError as e:
        CLIErrorHandler.handle_validation_error(e, json_output, telegram_string)
