"""Conbus client operations CLI commands."""

import click
import json
import threading

from ...services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from ..utils.decorators import connection_command, handle_service_errors
from ..utils.error_handlers import CLIErrorHandler
from .conbus import conbus


@conbus.command("scan")
@click.argument("serial_number", type=str)
@click.argument("function_code", type=int)
@click.option(
    "--background",
    "-b",
    default=True,
    is_flag=True,
    help="Run scan in background with live output",
)
@connection_command()
@handle_service_errors(ConbusClientSendError)
def scan_module(
    serial_number: str, function_code: str, json_output: bool, background: bool
):
    """
    Scan all datapoints of a function_code for a module.

    Examples:

    \b
        xp conbus scan 0020030837 02 # Scan all datapoints of function Read data points (02)
    """
    service = ConbusClientSendService()

    # Shared state for results collection and live output
    results = []
    successful_count = 0
    failed_count = 0

    def progress_callback(response, count, total):
        nonlocal successful_count, failed_count
        results.append(response)

        if not json_output:
            # Display results immediately as they arrive
            if response.success and response.sent_telegram:
                timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                click.echo(f"{timestamp} [TX] {response.sent_telegram}")
                successful_count += 1

                # Show responses if any
                for received in response.received_telegrams:
                    timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                    click.echo(f"{timestamp} [RX] {received}")
            else:
                failed_count += 1

            # Show progress every 1000 scans
            if count % 1000 == 0:
                progress_pct = (count / total) * 100
                click.echo(
                    f"Progress: {count}/{total} ({progress_pct:.1f}%) - Success: {successful_count}, Failed: {failed_count}"
                )

    try:
        with service:
            if background:
                # Background processing with live output
                if not json_output:
                    click.echo(f"Starting background scan of module {serial_number}...")
                    click.echo(
                        "Results will appear in real-time as they arrive from the server."
                    )
                    click.echo("Press Ctrl+C to stop the scan.\n")

                # Use background scanning with progress callback
                scan_complete = threading.Event()

                def background_scan():
                    try:
                        service.scan_module(
                            serial_number, function_code, progress_callback
                        )
                    except Exception as e:
                        if not json_output:
                            click.echo(f"Error during scan: {e}", err=True)
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
                    if not json_output:
                        click.echo("\nScan interrupted by user.")
                        click.echo(
                            f"Partial results: {successful_count} successful, {failed_count} failed scans"
                        )
                    raise click.Abort()

                # Wait for thread to complete
                scan_thread.join(timeout=1.0)

            else:
                # Traditional synchronous scanning
                results = service.scan_module(
                    serial_number,
                    function_code,
                    progress_callback if not json_output else None,
                )
                successful_count = len([r for r in results if r.success])
                failed_count = len([r for r in results if not r.success])

        # Final output
        if json_output:
            output = {
                "serial_number": serial_number,
                "total_scans": len(results),
                "successful_scans": successful_count,
                "failed_scans": failed_count,
                "background_mode": background,
                "results": [result.to_dict() for result in results],
            }
            click.echo(json.dumps(output, indent=2))
        else:
            if (
                not background
            ):  # Only show summary if not already shown during background processing
                click.echo(
                    f"\nScan completed: {successful_count}/{len(results)} telegrams sent successfully"
                )
            else:
                click.echo(
                    f"\nBackground scan completed: {successful_count} successful, {failed_count} failed scans"
                )

    except ConbusClientSendError as e:
        if "Connection timeout" in str(e):
            if not json_output:
                click.echo(
                    f"Connecting to {service.config.ip}:{service.config.port}..."
                )
                click.echo(
                    f"Error: Connection timeout after {service.config.timeout} seconds"
                )
                click.echo("Failed to connect to server")
            CLIErrorHandler.handle_connection_error(
                e,
                json_output,
                {
                    "ip": service.config.ip,
                    "port": service.config.port,
                    "timeout": service.config.timeout,
                },
            )
        else:
            CLIErrorHandler.handle_service_error(
                e,
                json_output,
                "module scan",
                {"serial_number": serial_number, "background_mode": background},
            )
    except click.Abort:
        # User interrupted the scan
        raise
