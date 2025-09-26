"""Conbus client operations CLI commands."""

import json
import threading

import click

from .conbus import conbus
from ..utils.decorators import connection_command, handle_service_errors
from ..utils.serial_number_type import SERIAL
from ...services.conbus_datapoint_service import (
    ConbusDatapointError,
)
from ...services.conbus_scan_service import ConbusScanService
from ...models import ConbusResponse


@conbus.command("scan")
@click.argument("serial_number", type=SERIAL)
@click.argument("function_code", type=str)
@click.option(
    "--background",
    "-b",
    default=True,
    is_flag=True,
    help="Run scan in background with live output",
)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def scan_module(serial_number: str, function_code: str, background: bool) -> None:
    """
    Scan all datapoints of a function_code for a module.

    Examples:

    \b
        xp conbus scan 0012345011 02 # Scan all datapoints of function Read data points (02)
    """
    service = ConbusScanService()

    # Shared state for results collection and live output
    results = []
    successful_count = 0
    failed_count = 0

    def progress_callback(response: ConbusResponse, total: int, count: int) -> None:
        nonlocal successful_count, failed_count
        results.append(response)

        if count % 10 == 0:
            click.echo(f"{count}/{total} datapoints scanned.")

        # Count results for JSON output
        if response.success:
            successful_count += 1
        else:
            failed_count += 1

    try:
        with service:
            if background:
                # Background processing

                # Use background scanning with progress callback
                scan_complete = threading.Event()

                def background_scan() -> None:
                    try:
                        service.scan_module(
                            serial_number, function_code, progress_callback
                        )
                    except (ValueError, KeyError, ConnectionError):
                        pass  # Will be handled by outer error handling
                    finally:
                        scan_complete.set()

                # Start background thread
                scan_thread = threading.Thread(target=background_scan, daemon=True)
                scan_thread.start()

                # Wait for completion or user interrupt
                try:
                    while not scan_complete.is_set():
                        scan_complete.wait(1.0)  # Check every second
                except KeyboardInterrupt:
                    # Output partial results in JSON format
                    output = {
                        "serial_number": serial_number,
                        "total_scans": len(results),
                        "successful_scans": successful_count,
                        "failed_scans": failed_count,
                        "background_mode": background,
                        "interrupted": True,
                        "results": [result.to_dict() for result in results],
                    }
                    click.echo(json.dumps(output, indent=2))
                    raise click.Abort()

                # Wait for thread to complete
                scan_thread.join(timeout=1.0)

            else:
                # Traditional synchronous scanning
                results = service.scan_module(
                    serial_number,
                    function_code,
                    progress_callback,
                )
                successful_count = len([r for r in results if r.success])
                failed_count = len([r for r in results if not r.success])

        # Final output
        output = {
            "serial_number": serial_number,
            "total_scans": len(results),
            "successful_scans": successful_count,
            "failed_scans": failed_count,
            "background_mode": background,
            "results": [result.to_dict() for result in results],
        }
        click.echo(json.dumps(output, indent=2))

    except click.Abort:
        # User interrupted the scan
        raise
