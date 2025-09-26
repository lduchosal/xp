"""File operations CLI commands for console bus logs."""

import click
import json
from click_help_colors import HelpColorsGroup

from ..utils.decorators import (
    file_operation_command,
    handle_service_errors,
)
from ..utils.formatters import StatisticsFormatter, OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def file() -> None:
    """
    File operations for console bus logs
    """
    pass


@file.command("decode")
@click.argument("log_file_path")
@click.option("--summary", is_flag=True, help="Show summary statistics only")
@file_operation_command()
@handle_service_errors(Exception)
def decode_log_file(
    log_file_path: str,
    filter_type: str,
    filter_direction: str,
    time_range: str,
    summary: bool,
) -> None:
    """
    Decode and parse console bus log file.

    Examples:

    \b
        xp file decode conbus.log
    """
    from ...services.log_file_service import LogFileService
    from ...utils.time_utils import parse_time_range, TimeParsingError

    service = LogFileService()
    StatisticsFormatter(True)

    try:
        # Parse the log file
        entries = service.parse_log_file(log_file_path)

        # Apply filters
        if filter_type or filter_direction or time_range:
            start_time = None
            end_time = None

            if time_range:
                try:
                    start_time, end_time = parse_time_range(time_range)
                except TimeParsingError as e:
                    error_response = OutputFormatter(True).error_response(
                        f"Invalid time range: {e}"
                    )
                    click.echo(error_response)
                    raise SystemExit(1)

            entries = service.filter_entries(
                entries,
                telegram_type=filter_type,
                direction=filter_direction,
                start_time=start_time,
                end_time=end_time,
            )

        # Generate statistics
        stats = service.get_file_statistics(entries)

        if summary:
            # Show summary only
            click.echo(
                json.dumps({"statistics": stats, "entry_count": len(entries)}, indent=2)
            )
        else:
            # Show full results
            output = {
                "file_path": log_file_path,
                "statistics": stats,
                "entries": [entry.to_dict() for entry in entries],
            }
            click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_file_error(e, log_file_path, "log file parsing")


@file.command("analyze")
@click.argument("log_file_path")
@handle_service_errors(Exception)
def analyze_log_file(log_file_path: str) -> None:
    """
    Analyze console bus log file for patterns and statistics.

    Examples:

    \b
        xp file analyze conbus.log
    """
    from ...services.log_file_service import LogFileService

    service = LogFileService()
    StatisticsFormatter(True)

    try:
        entries = service.parse_log_file(log_file_path)
        stats = service.get_file_statistics(entries)

        click.echo(
            json.dumps({"file_path": log_file_path, "analysis": stats}, indent=2)
        )

    except Exception as e:
        CLIErrorHandler.handle_file_error(e, log_file_path, "log file analysis")


@file.command("validate")
@click.argument("log_file_path")
@handle_service_errors(Exception)
def validate_log_file(log_file_path: str) -> None:
    """
    Validate console bus log file format and telegram checksums.

    Examples:

    \b
        xp file validate conbus.log
    """
    from ...services.log_file_service import LogFileService

    service = LogFileService()
    OutputFormatter(True)

    try:
        entries = service.parse_log_file(log_file_path)
        stats = service.get_file_statistics(entries)

        is_valid = stats["parse_errors"] == 0
        checksum_issues = stats["checksum_validation"]["invalid_checksums"]

        result = {
            "file_path": log_file_path,
            "valid_format": is_valid,
            "parse_errors": stats["parse_errors"],
            "checksum_issues": checksum_issues,
            "statistics": stats,
            "success": is_valid and checksum_issues == 0,
        }
        click.echo(json.dumps(result, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_file_error(e, log_file_path, "log file validation")
