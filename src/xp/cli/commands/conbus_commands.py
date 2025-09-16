"""Conbus client operations CLI commands."""
from pickle import BINPUT

import click
import json
import re
import threading
import time

from ...models.system_telegram import SystemFunction
from ...services.conbus_client_send_service import ConbusClientSendService, ConbusClientSendError
from ...services.input_service import XPInputService, XPInputError
from ...services.blink_service import BlinkService, BlinkError
from ...models.conbus_client_send import TelegramType, ConbusSendRequest
from ...models.input_telegram import ActionType
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


@conbus.command("input")
@click.argument('serial_number')
@click.argument('input_number_or_status')
@click.argument('on_or_off')
@connection_command()
@handle_service_errors(ConbusClientSendError)
def xp_input(serial_number: str, input_number_or_status: str, on_or_off: str, json_output: bool):
    """
    Send input command to XP module or query status.
    
    Examples:
    xp conbus input 0020044964 0 ON       # Toggle input 0
    xp conbus input 0020044964 1 OFF      # Toggle input 1
    xp conbus input 0020044964 2 ON       # Toggle input 2
    xp conbus input 0020044964 3 ON       # Toggle input 3
    xp conbus input 0020044964 status   # Query input status
    """
    service = ConbusClientSendService()
    input_service = XPInputService()
    
    try:
        with service:
            if input_number_or_status.lower() == 'status':
                # Send status query using custom telegram method
                response = service.send_custom_telegram(
                    serial_number, 
                    input_service.STATUS_FUNCTION,  # "02"
                    input_service.STATUS_DATAPOINT  # "12"
                )
                
                if json_output:
                    # Add XP24-specific data to response
                    response_data = response.to_dict()
                    response_data['xp24_operation'] = 'status_query'
                    response_data['telegram_type'] = 'xp_input'
                    
                    # Parse status from response if available
                    if response.success and response.received_telegrams:
                        try:
                            status = input_service.parse_status_response(response.received_telegrams[0])
                            response_data['input_status'] = status
                        except XPInputError:
                            # Status parsing failed, keep raw response
                            pass
                    
                    click.echo(json.dumps(response_data, indent=2))
                else:
                    if response.success:
                        # Format output like conbus examples
                        if response.sent_telegram:
                            timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                            click.echo(f"{timestamp} [TX] {response.sent_telegram}")
                        
                        # Show received telegrams and parse status
                        for received in response.received_telegrams:
                            timestamp = response.timestamp.strftime('%H:%M:%S,%f')[:-3]
                            click.echo(f"{timestamp} [RX] {received}")
                            
                            # Parse and display status in human-readable format
                            try:
                                status = input_service.parse_status_response(received)
                                status_summary = input_service.format_status_summary(status)
                                click.echo(f"\n{status_summary}")
                            except XPInputError:
                                # Status parsing failed, skip formatting
                                pass
                        
                        if not response.received_telegrams:
                            click.echo("No response received")
                    else:
                        click.echo(f"Error: {response.error}")
            
            else:
                # Parse input number and send action
                try:
                    input_number = int(input_number_or_status)
                    input_service.validate_input_number(input_number)
                except (ValueError, XPInputError) as e:
                    error_msg = f"Invalid input number: {input_number_or_status}"
                    if json_output:
                        error_response = {
                            "success": False,
                            "error": error_msg,
                            "valid_inputs": [0, 1, 2, 3],
                            "xp24_operation": "action_command"
                        }
                        click.echo(json.dumps(error_response, indent=2))
                        raise SystemExit(1)
                    else:
                        click.echo(f"Error: {error_msg}", err=True)
                        click.echo("Valid inputs: 0, 1, 2, 3 or 'status'")
                        raise click.ClickException("Invalid input number")
                
                # Send action telegram using custom telegram method
                # Format: F27D{input:02d}AA (Function 27, input number, PRESS action)
                action_type = ActionType.RELEASE.value
                if on_or_off.lower() == 'on':
                    action_type = ActionType.PRESS.value

                data_point_code = f"{input_number:02d}{action_type}"
                response = service.send_custom_telegram(
                    serial_number,
                    input_service.ACTION_FUNCTION,  # "27"
                    data_point_code  # "00AA", "01AA", etc.
                )
                
                if json_output:
                    # Add XP24-specific data to response
                    response_data = response.to_dict()
                    response_data['xp24_operation'] = 'action_command'
                    response_data['input_number'] = input_number
                    response_data['action_type'] = 'press'
                    response_data['telegram_type'] = 'xp24_action'
                    click.echo(json.dumps(response_data, indent=2))
                else:
                    if response.success:
                        # Format output like conbus examples
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
                            click.echo(f"XP24 action sent: Press input {input_number}")
                    else:
                        click.echo(f"Error: {response.error}")
                
    except XPInputError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "xp24_operation": "validation_error"
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"XP24 Error: {e}", err=True)
            raise click.ClickException(str(e))
            
    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(e, json_output, "XP Input", {
            "serial_number": serial_number,
            "input_number_or_status": input_number_or_status,
            "on_or_off": on_or_off,
        })


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

@conbus.command("blink")
@click.argument('serial_number')
@click.argument('on_or_off')
@connection_command()
@handle_service_errors(ConbusClientSendError, BlinkError)
def send_blink_telegram(serial_number: str, on_or_off: str, json_output: bool):
    """
    Send blink command to start blinking module LED.
    
    Example: xp conbus blink 0020044964
    """
    conbus_service = ConbusClientSendService()
    blink_service = BlinkService()
    
    try:
        # Validate serial number using blink service
        blink_service.generate_blink_telegram(serial_number)  # This validates the serial

        # Blink is 05, Unblink is 06
        function_code = SystemFunction.UNBLINK.value
        if on_or_off.lower() == 'on':
            function_code = SystemFunction.BLINK.value

        # Send blink telegram using custom method (F05D00)
        with conbus_service:
            response = conbus_service.send_custom_telegram(
                serial_number, 
                function_code,  # Blink or Unblink function code
                "00"   # Status data point
            )
        
        if json_output:
            response_data = response.to_dict()
            response_data['operation'] = 'blink'
            response_data['blink_operation'] = 'start_blinking'
            click.echo(json.dumps(response_data, indent=2))
        else:
            if response.success:
                # Format output like other conbus commands
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
                    click.echo(f"Blink command sent to module {serial_number}")
            else:
                click.echo(f"Error: {response.error}")
                
    except BlinkError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "operation": "blink",
                "serial_number": serial_number
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Blink Error: {e}", err=True)
            raise click.ClickException(str(e))
            
    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(e, json_output, "blink command", {
            "serial_number": serial_number,
            "operation": "blink"
        })
