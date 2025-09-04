"""Conbus client operations CLI commands."""
import click
import json
import threading
import time

from ...services.conbus_client_send_service import ConbusClientSendService, ConbusClientSendError
from ...models.conbus_client_send import TelegramType, ConbusSendRequest
from ..utils.decorators import json_output_option, connection_command, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def conbus():
    """Conbus client operations for sending telegrams to remote servers"""
    pass


@conbus.command("config")
@json_output_option
@handle_service_errors(Exception)
def show_config(json_output: bool):
    """
    Display current Conbus client configuration.
    
    Example: xp conbus config
    """
    service = ConbusClientSendService()
    formatter = OutputFormatter(json_output)
    
    try:
        config = service.get_config()
        
        if json_output:
            click.echo(json.dumps(config.to_dict(), indent=2))
        else:
            click.echo(f"  ip: {config.ip}")
            click.echo(f"  port: {config.port}")
            click.echo(f"  timeout: {config.timeout} seconds")
            
    except Exception as e:
        CLIErrorHandler.handle_service_error(e, json_output, "configuration retrieval")


@conbus.command("send")
@click.argument('target_serial')
@click.argument('telegram_type')
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_telegram(target_serial: str, telegram_type: str, json_output: bool):
    """
    Send telegram to Conbus server.

    Examples:
    xp conbus send 0000000000 discovery
    xp conbus send 0020030837 version
    xp conbus send 0020030837 voltage
    xp conbus send 0020030837 temperature
    xp conbus send 0020030837 current
    xp conbus send 0020030837 humidity
    """
    service = ConbusClientSendService()
    formatter = OutputFormatter(json_output)

    try:
        # Validate arguments
        if target_serial is None:
            error_response = formatter.error_response("target_serial is required")
            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo("Error: target_serial is required", err=True)
                raise click.ClickException("Missing target_serial")

        if telegram_type is None:
            error_response = formatter.error_response("Telegram type required")
            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo("Error: Telegram type required", err=True)
                raise click.ClickException("Missing telegram type")

        # Map string to enum
        telegram_type_map = {
            "discovery": TelegramType.DISCOVERY,
            "version": TelegramType.VERSION,
            "voltage": TelegramType.VOLTAGE,
            "temperature": TelegramType.TEMPERATURE,
            "current": TelegramType.CURRENT,
            "humidity": TelegramType.HUMIDITY
        }

        telegram_type_enum = telegram_type_map.get(telegram_type.lower())
        if not telegram_type_enum:
            error_data = {
                "telegram_type": telegram_type,
                "valid_types": list(telegram_type_map.keys())
            }
            error_response = formatter.error_response(f"Unknown telegram type: {telegram_type}", error_data)
            
            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo(f"Error: Unknown telegram type: {telegram_type}", err=True)
                click.echo(f"Valid types: {', '.join(telegram_type_map.keys())}")
                raise click.ClickException("Invalid telegram type")

        # Create request
        request = ConbusSendRequest(
            telegram_type=telegram_type_enum,
            target_serial=target_serial
        )

        # Send telegram
        with service:
            response = service.send_telegram(request)

        if json_output:
            click.echo(json.dumps(response.to_dict(), indent=2))
        else:
            if response.success:
                # Format output like the specification examples
                if response.sent_telegram:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [TX] {response.sent_telegram}")

                # Show received telegrams
                for received in response.received_telegrams:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [RX] {received}")

                if not response.received_telegrams:
                    click.echo("No response received")
            else:
                click.echo(f"Error: {response.error}")

    except ConbusClientSendError as e:
        if "Connection timeout" in str(e):
            if not json_output:
                click.echo(f"Connecting to {service.config.ip}:{service.config.port}...")
                click.echo(f"Error: Connection timeout after {service.config.timeout} seconds")
                click.echo("Failed to connect to server")
            CLIErrorHandler.handle_connection_error(e, json_output, {
                "ip": service.config.ip,
                "port": service.config.port,
                "timeout": service.config.timeout
            })
        else:
            CLIErrorHandler.handle_service_error(e, json_output, "telegram send")


@conbus.command("discover")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_discover_telegram(json_output: bool):
    """
    Send discovery telegram to Conbus server.

    Examples:
    xp conbus discover
    """
    service = ConbusClientSendService()

    try:
        # Discovery telegram
        telegram_type_enum = TelegramType.DISCOVERY
        target_serial = None

        # Create request
        request = ConbusSendRequest(
            telegram_type=telegram_type_enum,
            target_serial=target_serial
        )

        # Send telegram
        with service:
            response = service.send_telegram(request)

        if json_output:
            click.echo(json.dumps(response.to_dict(), indent=2))
        else:
            if response.success:
                # Format output like the specification examples
                if response.sent_telegram:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [TX] {response.sent_telegram}")

                # Show received telegrams
                for received in response.received_telegrams:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [RX] {received}")

                if not response.received_telegrams:
                    click.echo("No response received")
            else:
                click.echo(f"Error: {response.error}")

    except ConbusClientSendError as e:
        if "Connection timeout" in str(e):
            if not json_output:
                click.echo(f"Connecting to {service.config.ip}:{service.config.port}...")
                click.echo(f"Error: Connection timeout after {service.config.timeout} seconds")
                click.echo("Failed to connect to server")
            CLIErrorHandler.handle_connection_error(e, json_output, {
                "ip": service.config.ip,
                "port": service.config.port,
                "timeout": service.config.timeout
            })
        else:
            CLIErrorHandler.handle_service_error(e, json_output, "discovery telegram send")


@conbus.command("scan")
@click.argument('serial_number')
@click.argument('function_code')
@click.option('--background', '-b', default=True, is_flag=True, help='Run scan in background with live output')
@connection_command()
@handle_service_errors(ConbusClientSendError)
def scan_module(serial_number: str, function_code: str, json_output: bool, background: bool):
    """
    Scan all datapoints of a function_code for a module.
    
    Example: xp conbus scan 0020030837 02
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
                timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                click.echo(f"{timestamp} [TX] {response.sent_telegram}")
                successful_count += 1
                
                # Show responses if any
                for received in response.received_telegrams:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [RX] {received}")
            else:
                failed_count += 1
            
            # Show progress every 1000 scans
            if count % 1000 == 0:
                progress_pct = (count / total) * 100
                click.echo(f"Progress: {count}/{total} ({progress_pct:.1f}%) - Success: {successful_count}, Failed: {failed_count}")
    
    try:
        with service:
            if background:
                # Background processing with live output
                if not json_output:
                    click.echo(f"Starting background scan of module {serial_number}...")
                    click.echo("Results will appear in real-time as they arrive from the server.")
                    click.echo("Press Ctrl+C to stop the scan.\n")
                
                # Use background scanning with progress callback
                scan_complete = threading.Event()
                
                def background_scan():
                    try:
                        service.scan_module(serial_number, function_code, progress_callback)
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
                        click.echo(f"\nScan interrupted by user.")
                        click.echo(f"Partial results: {successful_count} successful, {failed_count} failed scans")
                    raise click.Abort()
                
                # Wait for thread to complete
                scan_thread.join(timeout=1.0)
                
            else:
                # Traditional synchronous scanning
                results = service.scan_module(serial_number, function_code, progress_callback if not json_output else None)
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
                "results": [result.to_dict() for result in results]
            }
            click.echo(json.dumps(output, indent=2))
        else:
            if not background:  # Only show summary if not already shown during background processing
                click.echo(f"\nScan completed: {successful_count}/{len(results)} telegrams sent successfully")
            else:
                click.echo(f"\nBackground scan completed: {successful_count} successful, {failed_count} failed scans")
            
    except ConbusClientSendError as e:
        if "Connection timeout" in str(e):
            if not json_output:
                click.echo(f"Connecting to {service.config.ip}:{service.config.port}...")
                click.echo(f"Error: Connection timeout after {service.config.timeout} seconds")
                click.echo("Failed to connect to server")
            CLIErrorHandler.handle_connection_error(e, json_output, {
                "ip": service.config.ip,
                "port": service.config.port,
                "timeout": service.config.timeout
            })
        else:
            CLIErrorHandler.handle_service_error(e, json_output, "module scan", {
                "serial_number": serial_number,
                "background_mode": background
            })
    except click.Abort:
        # User interrupted the scan
        raise


@conbus.command("custom")
@click.argument('serial_number')
@click.argument('function_code')
@click.argument('data_point_code')
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_custom_telegram(serial_number: str, function_code: str, data_point_code: str, json_output: bool):
    """
    Send custom telegram with specified function and data point codes.
    
    Example: xp conbus custom 0020030837 02 E2
    """
    service = ConbusClientSendService()
    
    try:
        with service:
            response = service.send_custom_telegram(serial_number, function_code, data_point_code)
        
        if json_output:
            click.echo(json.dumps(response.to_dict(), indent=2))
        else:
            if response.success:
                # Format output like the specification examples  
                if response.sent_telegram:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [TX] {response.sent_telegram}")
                
                # Show received telegrams
                for received in response.received_telegrams:
                    timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                    click.echo(f"{timestamp} [RX] {received}")
                
                if not response.received_telegrams:
                    click.echo("No response received")
            else:
                click.echo(f"Error: {response.error}")
                
    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(e, json_output, "custom telegram send", {
            "serial_number": serial_number,
            "function_code": function_code,
            "data_point_code": data_point_code
        })