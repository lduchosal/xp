"""File operations CLI commands for console bus logs."""

import click
import json

from ..utils.decorators import (
    json_output_option,
    file_operation_command,
    handle_service_errors,
)
from ..utils.formatters import StatisticsFormatter, OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def file():
    """File operations for console bus logs"""
    pass


@file.command("decode")
@click.argument("log_file_path")
@click.option("--summary", is_flag=True, help="Show summary statistics only")
@file_operation_command()
@handle_service_errors(Exception)
def decode_log_file(
    log_file_path: str,
    json_output: bool,
    filter_type: str,
    filter_direction: str,
    time_range: str,
    summary: bool,
):
    """
    Decode and parse console bus log file.

    Example: xp file decode conbus.log
    Example: xp file decode conbus.log --filter-type event --json-output
    """
    from ...services.log_file_service import LogFileService, LogFileParsingError
    from ...utils.time_utils import parse_time_range, TimeParsingError

    service = LogFileService()
    formatter = StatisticsFormatter(json_output)

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
                    error_response = OutputFormatter(json_output).error_response(
                        f"Invalid time range: {e}"
                    )
                    if json_output:
                        click.echo(error_response)
                        raise SystemExit(1)
                    else:
                        click.echo(f"Error: Invalid time range: {e}", err=True)
                        raise click.ClickException("Invalid time range format")

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
            if json_output:
                click.echo(
                    json.dumps(
                        {"statistics": stats, "entry_count": len(entries)}, indent=2
                    )
                )
            else:
                click.echo(
                    formatter.format_file_statistics(log_file_path, stats, len(entries))
                )
        else:
            # Show full results
            if json_output:
                output = {
                    "file_path": log_file_path,
                    "statistics": stats,
                    "entries": [entry.to_dict() for entry in entries],
                }
                click.echo(json.dumps(output, indent=2))
            else:
                click.echo(
                    formatter.format_file_statistics(log_file_path, stats, len(entries))
                )
                click.echo(f"\n=== Log Entries ===")
                for entry in entries:
                    click.echo(str(entry))

    except Exception as e:
        CLIErrorHandler.handle_file_error(
            e, json_output, log_file_path, "log file parsing"
        )


@file.command("analyze")
@click.argument("log_file_path")
@json_output_option
@handle_service_errors(Exception)
def analyze_log_file(log_file_path: str, json_output: bool):
    """
    Analyze console bus log file for patterns and statistics.

    Example: xp file analyze conbus.log
    """
    from ...services.log_file_service import LogFileService, LogFileParsingError

    service = LogFileService()
    formatter = StatisticsFormatter(json_output)

    try:
        entries = service.parse_log_file(log_file_path)
        stats = service.get_file_statistics(entries)

        if json_output:
            click.echo(
                json.dumps({"file_path": log_file_path, "analysis": stats}, indent=2)
            )
        else:
            # Format analysis output
            click.echo(f"=== Console Bus Log Analysis ===")
            click.echo(f"File: {log_file_path}")

            if stats.get("time_range", {}).get("start"):
                click.echo(
                    f"Time Range: {stats['time_range']['start']} - {stats['time_range']['end']}"
                )
                click.echo(
                    f"Duration: {stats['time_range']['duration_seconds']:.3f} seconds"
                )

            click.echo(f"\nParsing Results:")
            click.echo(f"  Total Entries: {stats['total_entries']}")
            click.echo(f"  Successfully Parsed: {stats['valid_parses']}")
            click.echo(f"  Parse Errors: {stats['parse_errors']}")
            click.echo(f"  Parse Success Rate: {stats['parse_success_rate']:.1f}%")

            click.echo(f"\nChecksum Validation:")
            cv = stats["checksum_validation"]
            click.echo(f"  Validated Telegrams: {cv['validated_count']}")
            click.echo(f"  Valid Checksums: {cv['valid_checksums']}")
            click.echo(f"  Invalid Checksums: {cv['invalid_checksums']}")
            click.echo(
                f"  Validation Success Rate: {cv['validation_success_rate']:.1f}%"
            )

            click.echo(f"\nTelegram Types:")
            type_counts = stats["telegram_type_counts"]
            for t_type, count in type_counts.items():
                percentage = (
                    (count / stats["total_entries"] * 100)
                    if stats["total_entries"] > 0
                    else 0
                )
                click.echo(f"  {t_type.capitalize()}: {count} ({percentage:.1f}%)")

            click.echo(f"\nDirection Distribution:")
            dir_counts = stats["direction_counts"]
            for direction, count in dir_counts.items():
                percentage = (
                    (count / stats["total_entries"] * 100)
                    if stats["total_entries"] > 0
                    else 0
                )
                click.echo(f"  {direction.upper()}: {count} ({percentage:.1f}%)")

            if stats.get("devices"):
                click.echo(f"\nDevices Found:")
                for device in stats["devices"]:
                    click.echo(f"  {device}")

    except Exception as e:
        CLIErrorHandler.handle_file_error(
            e, json_output, log_file_path, "log file analysis"
        )


@file.command("validate")
@click.argument("log_file_path")
@json_output_option
@handle_service_errors(Exception)
def validate_log_file(log_file_path: str, json_output: bool):
    """
    Validate console bus log file format and telegram checksums.

    Example: xp file validate conbus.log
    """
    from ...services.log_file_service import LogFileService, LogFileParsingError

    service = LogFileService()
    formatter = OutputFormatter(json_output)

    try:
        entries = service.parse_log_file(log_file_path)
        stats = service.get_file_statistics(entries)

        is_valid = stats["parse_errors"] == 0
        checksum_issues = stats["checksum_validation"]["invalid_checksums"]

        if json_output:
            result = {
                "file_path": log_file_path,
                "valid_format": is_valid,
                "parse_errors": stats["parse_errors"],
                "checksum_issues": checksum_issues,
                "statistics": stats,
                "success": is_valid and checksum_issues == 0,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            # Format validation output
            click.echo(f"=== Console Bus Log Validation ===")
            click.echo(f"File: {log_file_path}")

            status = "✓ VALID" if is_valid else "✗ INVALID"
            click.echo(f"Format Status: {status}")

            if stats["parse_errors"] > 0:
                click.echo(f"\nParse Errors Found: {stats['parse_errors']}")
                error_entries = [e for e in entries if e.parse_error]
                for entry in error_entries[:5]:  # Show first 5 errors
                    click.echo(f"  Line {entry.line_number}: {entry.parse_error}")

                if len(error_entries) > 5:
                    click.echo(f"  ... and {len(error_entries) - 5} more errors")

            cv = stats["checksum_validation"]
            if cv["invalid_checksums"] > 0:
                click.echo(
                    f"\nChecksum Issues: {cv['invalid_checksums']} invalid checksums found"
                )
                invalid_entries = [e for e in entries if e.checksum_validated is False]
                for entry in invalid_entries[:5]:  # Show first 5 checksum errors
                    click.echo(f"  Line {entry.line_number}: {entry.raw_telegram}")

                if len(invalid_entries) > 5:
                    click.echo(
                        f"  ... and {len(invalid_entries) - 5} more checksum errors"
                    )

            if is_valid and cv["invalid_checksums"] == 0:
                click.echo(f"\n✓ All telegrams parsed successfully")
                click.echo(f"✓ All checksums validated successfully")

    except Exception as e:
        CLIErrorHandler.handle_file_error(
            e, json_output, log_file_path, "log file validation"
        )
