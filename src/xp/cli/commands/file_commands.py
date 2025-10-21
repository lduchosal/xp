"""File operations CLI commands for console bus logs."""

import json

import click
from click import Context
from click_help_colors import HelpColorsGroup

from xp.cli.utils.decorators import (
    file_operation_command,
    handle_service_errors,
)
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import OutputFormatter, StatisticsFormatter


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def file() -> None:
    """Perform file operations for console bus logs."""
    pass


@file.command("decode")
@click.argument("log_file_path")
@click.option("--summary", is_flag=True, help="Show summary statistics only")
@click.pass_context
@file_operation_command()
@handle_service_errors(Exception)
def decode_log_file(
    ctx: Context,
    log_file_path: str,
    filter_type: str,
    filter_direction: str,
    time_range: str,
    summary: bool,
) -> None:
    r"""Decode and parse console bus log file.

    Args:
        ctx: Click context object.
        log_file_path: Path to the log file to decode.
        filter_type: Filter by telegram type.
        filter_direction: Filter by telegram direction.
        time_range: Filter by time range.
        summary: Show summary statistics only.

    Examples:
        \b
        xp file decode conbus.log

    Raises:
        SystemExit: If time range is invalid or log file cannot be parsed.
    """
    from xp.services.log_file_service import LogFileService
    from xp.utils.time_utils import TimeParsingError, parse_time_range

    service: LogFileService = (
        ctx.obj.get("container").get_container().resolve(LogFileService)
    )
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
@click.pass_context
@handle_service_errors(Exception)
def analyze_log_file(ctx: Context, log_file_path: str) -> None:
    r"""Analyze console bus log file for patterns and statistics.

    Args:
        ctx: Click context object.
        log_file_path: Path to the log file to analyze.

    Examples:
        \b
        xp file analyze conbus.log
    """
    from xp.services.log_file_service import LogFileService

    service: LogFileService = (
        ctx.obj.get("container").get_container().resolve(LogFileService)
    )
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
@click.pass_context
@handle_service_errors(Exception)
def validate_log_file(ctx: Context, log_file_path: str) -> None:
    r"""Validate console bus log file format and telegram checksums.

    Args:
        ctx: Click context object.
        log_file_path: Path to the log file to validate.

    Examples:
        \b
        xp file validate conbus.log
    """
    from xp.services.log_file_service import LogFileService

    service: LogFileService = (
        ctx.obj.get("container").get_container().resolve(LogFileService)
    )
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
