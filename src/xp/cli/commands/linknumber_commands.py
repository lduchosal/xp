"""Link number operations CLI commands."""

import click
import json

from ...services.link_number_service import LinkNumberService, LinkNumberError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def linknumber():
    """
    Link number operations for module configuration
    """
    pass


@linknumber.command("generate")
@click.argument("serial_number")
@click.argument("link_number", type=int)
@json_output_option
@handle_service_errors(LinkNumberError)
def generate_set_link_number(serial_number: str, link_number: int, json_output: bool):
    """
    Generate a telegram to set module link number.

    Examples:

    \b
        xp linknumber generate 0020044974 25
    """
    service = LinkNumberService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_set_link_number_telegram(serial_number, link_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "link_number": link_number,
                "operation": "set_link_number",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Set Link Number Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Link Number: {link_number}")
            click.echo(f"Telegram: {telegram}")

    except LinkNumberError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "link number telegram generation",
            {"serial_number": serial_number, "link_number": link_number},
        )


@linknumber.command("read")
@click.argument("serial_number")
@json_output_option
@handle_service_errors(LinkNumberError)
def generate_read_link_number(serial_number: str, json_output: bool):
    """
    Generate a telegram to read module link number.

    Examples:

    \b
        xp linknumber read 0020044974
    """
    service = LinkNumberService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_read_link_number_telegram(serial_number)

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "read_link_number",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Read Link Number Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")

    except LinkNumberError as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "read telegram generation", {"serial_number": serial_number}
        )


@linknumber.command("parse")
@click.argument("telegram_list", nargs=-1, required=True)
@json_output_option
@handle_service_errors(TelegramParsingError, LinkNumberError)
def parse_link_number_telegrams(telegram_list: tuple, json_output: bool):
    """
    Parse link number related telegrams (system and reply).

    Examples:

    \b
        xp linknumber parse "<S0020044974F04D0425FO>" "<R0020044974F18DFB>"
        xp linknumber parse "<S0020044974F04D0409FA>" "<R0020044974F19DFA>"
    """
    telegram_service = TelegramService()
    link_service = LinkNumberService()
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
                if link_service.is_ack_response(parsed):
                    result["response_type"] = "ACK"
                    result["status"] = "Acknowledged"
                elif link_service.is_nak_response(parsed):
                    result["response_type"] = "NAK"
                    result["status"] = "Not Acknowledged"
                else:
                    # Try to parse link number value
                    link_num = link_service.parse_link_number_from_reply(parsed)
                    if link_num is not None:
                        result["link_number"] = link_num
                        result["status"] = "Link Number Response"

            results.append(result)

        except (TelegramParsingError, LinkNumberError) as e:
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
        click.echo("=== Link Number Telegram Analysis ===")
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
                elif "link_number" in result:
                    click.echo(f"   → Link Number: {result['link_number']}")
                elif "parsed" in result:
                    parsed_info = result["parsed"]
                    if "system_function" in parsed_info:
                        func_desc = parsed_info["system_function"]["description"]
                        data_desc = parsed_info["data_point_id"]["description"]
                        click.echo(f"   → Function: {func_desc} for {data_desc}")

            click.echo()
