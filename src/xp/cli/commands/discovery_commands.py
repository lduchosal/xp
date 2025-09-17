"""Device discovery operations CLI commands."""

import click
import json

from ...services.discovery_service import DiscoveryService, DiscoveryError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter, ListFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def discovery():
    """
    Device discovery operations for console bus enumeration
    """
    pass


@discovery.command("generate")
@json_output_option
@handle_service_errors(DiscoveryError)
def generate_discovery(json_output: bool):
    """
    Generate a discovery telegram for device enumeration.

    Examples:

    \b
        xp discovery generate
    """
    service = DiscoveryService()
    OutputFormatter(json_output)

    try:
        telegram = service.generate_discovery_telegram()

        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "operation": "discovery_broadcast",
                "broadcast_address": "0000000000",
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Discovery Broadcast Telegram:")
            click.echo("Broadcast Address: 0000000000")
            click.echo(f"Telegram: {telegram}")
            click.echo(
                "\nUse this telegram to enumerate all devices on the console bus."
            )

    except DiscoveryError as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "discovery telegram generation"
        )


@discovery.command("parse")
@click.argument("telegram_list", nargs=-1, required=True)
@click.option("--summary", is_flag=True, help="Show summary only")
@json_output_option
@handle_service_errors(TelegramParsingError, DiscoveryError)
def parse_discovery_responses(telegram_list: tuple, json_output: bool, summary: bool):
    """
    Parse discovery response telegrams to identify discovered devices.

    Examples:

    \b
        xp discovery parse "<R0020030837F01DFM>" "<R0020044966F01DFK>"
        xp discovery parse --summary "<R0020030837F01DFM>" "<R0020044966F01DFK>"
    """
    telegram_service = TelegramService()
    discovery_service = DiscoveryService()
    ListFormatter(json_output)

    devices = []
    errors = []

    for telegram_str in telegram_list:
        try:
            # Parse the telegram
            if telegram_str.startswith("<R"):
                parsed = telegram_service.parse_reply_telegram(telegram_str)
                device_info = discovery_service.parse_discovery_response(parsed)

                if device_info:
                    devices.append(device_info)
                else:
                    errors.append(
                        {
                            "telegram": telegram_str,
                            "error": "Not a discovery response telegram",
                        }
                    )
            elif telegram_str.startswith("<S"):
                # Handle discovery request telegram
                parsed = telegram_service.parse_system_telegram(telegram_str)
                if parsed.system_function.value == "01":  # Discovery
                    if json_output or not summary:
                        pass  # Will be handled in output
                else:
                    errors.append(
                        {"telegram": telegram_str, "error": "Not a discovery telegram"}
                    )
            else:
                errors.append(
                    {"telegram": telegram_str, "error": "Invalid telegram format"}
                )

        except (TelegramParsingError, DiscoveryError) as e:
            errors.append({"telegram": telegram_str, "error": str(e)})

    if json_output:
        output = {
            "devices": [device.to_dict() for device in devices],
            "summary": discovery_service.generate_discovery_summary(devices),
            "errors": errors,
            "success": len(devices) > 0,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        if summary:
            if devices:
                click.echo(discovery_service.format_discovery_results(devices))
            else:
                click.echo("No devices discovered")
        else:
            # Detailed output
            click.echo("=== Discovery Response Analysis ===")
            click.echo(f"Processed {len(telegram_list)} telegram(s)")

            if devices:
                click.echo("\nDiscovered Devices:")
                click.echo("-" * 50)

                for i, device in enumerate(devices, 1):
                    status = "✓" if device.checksum_valid else "✗"
                    click.echo(f"{i}. {device.serial_number} ({status})")
                    click.echo(f"   Raw: {device.raw_telegram}")

            if errors:
                click.echo("\nErrors:")
                click.echo("-" * 50)
                for error in errors:
                    click.echo(f"✗ {error['telegram']}: {error['error']}")

            if devices:
                click.echo(f"\n{discovery_service.format_discovery_results(devices)}")


@discovery.command("analyze")
@click.argument("log_file_path")
@click.option("--time-range", help="Filter by time range (HH:MM:SS,mmm-HH:MM:SS,mmm)")
@json_output_option
@handle_service_errors(Exception)
def analyze_discovery_session(log_file_path: str, json_output: bool, time_range: str):
    """
    Analyze a console bus log file for discovery sessions.

    Examples:

    \b
        xp discovery analyze conbus-discover.log
        xp discovery analyze conbus.log --time-range "22:48:38,000-22:48:39,000"
    """
    from ...services.log_file_service import LogFileService
    from ...utils.time_utils import parse_time_range, TimeParsingError

    log_service = LogFileService()
    TelegramService()
    discovery_service = DiscoveryService()
    formatter = OutputFormatter(json_output)

    try:
        # Parse the log file
        entries = log_service.parse_log_file(log_file_path)

        # Apply time filter if specified
        if time_range:
            try:
                start_time, end_time = parse_time_range(time_range)
                entries = log_service.filter_entries(
                    entries, start_time=start_time, end_time=end_time
                )
            except TimeParsingError as e:
                error_response = formatter.error_response(f"Invalid time range: {e}")
                if json_output:
                    click.echo(error_response)
                    raise SystemExit(1)
                else:
                    click.echo(f"Error: Invalid time range: {e}", err=True)
                    raise click.ClickException("Invalid time range format")

        # Find discovery sessions
        discovery_requests = []
        discovery_responses = []

        for entry in entries:
            if entry.parsed_telegram and entry.parse_error is None:
                # Check for discovery system telegrams (requests)
                if hasattr(entry.parsed_telegram, "system_function") and not hasattr(
                    entry.parsed_telegram, "data_value"
                ):
                    if entry.parsed_telegram.system_function.value == "01":  # Discovery
                        discovery_requests.append(entry)

                # Check for discovery reply telegrams (responses)
                elif hasattr(entry.parsed_telegram, "data_value"):
                    if discovery_service.is_discovery_response(entry.parsed_telegram):
                        discovery_responses.append(entry)

        # Extract device information
        devices = []
        for response_entry in discovery_responses:
            device_info = discovery_service.parse_discovery_response(
                response_entry.parsed_telegram
            )
            if device_info:
                devices.append(device_info)

        summary = discovery_service.generate_discovery_summary(devices)

        if json_output:
            output = {
                "file_path": log_file_path,
                "discovery_requests": len(discovery_requests),
                "discovery_responses": len(discovery_responses),
                "devices": [device.to_dict() for device in devices],
                "summary": summary,
                "success": len(devices) > 0,
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("=== Discovery Session Analysis ===")
            click.echo(f"File: {log_file_path}")

            if time_range:
                click.echo(f"Time Range: {time_range}")

            click.echo(f"Discovery Requests: {len(discovery_requests)}")
            click.echo(f"Discovery Responses: {len(discovery_responses)}")

            if discovery_requests:
                click.echo("\nDiscovery Requests:")
                for req in discovery_requests[:3]:  # Show first 3
                    click.echo(
                        f"  {req.timestamp.strftime('%H:%M:%S,%f')[:-3]} [{req.direction}] {req.raw_telegram}"
                    )
                if len(discovery_requests) > 3:
                    click.echo(f"  ... and {len(discovery_requests) - 3} more")

            if devices:
                click.echo(f"\n{discovery_service.format_discovery_results(devices)}")
            else:
                click.echo("\nNo devices discovered in the log file.")

    except Exception as e:
        CLIErrorHandler.handle_file_error(
            e, json_output, log_file_path, "discovery analysis"
        )
