"""Blink operations CLI commands."""

import click
import json

from ...services.blink_service import BlinkService, BlinkError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def blink():
    """
    Blink operations for module LED control
    """
    pass


@blink.command("on")
@click.argument("serial_number")
@json_output_option
@handle_service_errors(BlinkError)
def blink_on(serial_number: str, json_output: bool):
    """
    Generate a telegram to start blinking module LED.

    Examples:

    \b
        xp blink on 0020044964
        xp blink on 0020044964
    """
    service = BlinkService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_blink_telegram(serial_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "blink_on",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Blink LED Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "blink telegram generation",
            {"serial_number": serial_number},
        )


@blink.command("off")
@click.argument("serial_number")
@json_output_option
@handle_service_errors(BlinkError)
def blink_off(serial_number: str, json_output: bool):
    """
    Generate a telegram to stop blinking module LED.

    Examples:

    \b
        xp blink off 0020030837
    """
    service = BlinkService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_unblink_telegram(serial_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "blink_off",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Unblink LED Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")

    except BlinkError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "unblink telegram generation",
            {"serial_number": serial_number},
        )


@blink.command("parse")
@click.argument("telegram_list", nargs=-1, required=True)
@json_output_option
@handle_service_errors(TelegramParsingError, BlinkError)
def parse_blink_telegrams(telegram_list: tuple, json_output: bool):
    """
    Parse blink related telegrams (system and reply).

    Examples:

    \b
        xp blink parse "<S0020044964F05D00FN>" "<R0020044964F18DFB>"
        xp blink parse "<S0020030837F06D00FJ>" "<R0020030837F19DFA>"
    """
    telegram_service = TelegramService()
    blink_service = BlinkService()
    OutputFormatter(json_output)

    results = []

    for telegram_str in telegram_list:
        try:
            # Parse the telegram
            parsed = telegram_service.parse_telegram(telegram_str)

            result = {
                "raw_telegram": telegram_str,
                "parsed": parsed.to_dict(),
                "telegram_type": parsed.to_dict().get("telegram_type", "unknown"),
            }

            # Add specific analysis for reply telegrams
            if hasattr(parsed, "data_value"):  # ReplyTelegram
                if blink_service.is_ack_response(parsed):
                    result["response_type"] = "ACK"
                    result["status"] = "Blink command acknowledged"
                elif blink_service.is_nak_response(parsed):
                    result["response_type"] = "NAK"
                    result["status"] = "Blink command not acknowledged"

            results.append(result)

        except (TelegramParsingError, BlinkError) as e:
            error_result = {
                "raw_telegram": telegram_str,
                "error": str(e),
                "success": False,
            }
            results.append(error_result)

    if json_output:
        output = {
            "results": results,
            "count": len(results),
            "success": all("error" not in r for r in results),
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo("=== Blink Telegram Analysis ===")
        click.echo(f"Parsed {len(results)} telegrams:")
        click.echo("-" * 60)

        for i, result in enumerate(results, 1):
            click.echo(f"{i}. {result['raw_telegram']}")

            if "error" in result:
                click.echo(f"   ✗ Error: {result['error']}")
            else:
                telegram_type = result["telegram_type"].capitalize()
                click.echo(f"   ✓ Type: {telegram_type}")

                if "response_type" in result:
                    click.echo(f"   → {result['response_type']}: {result['status']}")
                elif "parsed" in result:
                    parsed_info = result["parsed"]
                    if "system_function" in parsed_info:
                        func_desc = parsed_info["system_function"]["description"]
                        data_desc = parsed_info["data_point_id"]["description"]
                        click.echo(f"   → Function: {func_desc} for {data_desc}")

            click.echo()
