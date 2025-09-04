"""Version information operations CLI commands."""
import click
import json

from ...services.version_service import VersionService, VersionParsingError
from ...services.telegram_service import TelegramService, TelegramParsingError
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def version():
    """Version information operations for device firmware"""
    pass


@version.command("request")
@click.argument('serial_number')
@json_output_option
@handle_service_errors(VersionParsingError)
def generate_version_request(serial_number: str, json_output: bool):
    """
    Generate a telegram to request version information from a device.
    
    Example: xp version request 0020030837
    """
    service = VersionService()
    formatter = OutputFormatter(json_output)
    
    try:
        result = service.generate_version_request_telegram(serial_number)
        
        if not result.success:
            error_response = formatter.error_response(result.error, {"serial_number": serial_number})
            click.echo(error_response)
            if json_output:
                raise SystemExit(1)
            else:
                raise click.ClickException("Version request generation failed")
        
        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(f"Version Request Telegram:")
            click.echo(f"Serial: {result.data['serial_number']}")
            click.echo(f"Telegram: {result.data['telegram']}")
            click.echo(f"Function: {result.data['function_code']} (Return Data)")
            click.echo(f"Data Point: {result.data['data_point_code']} (Version)")
            click.echo(f"Checksum: {result.data['checksum']}")
            
    except VersionParsingError as e:
        CLIErrorHandler.handle_service_error(e, json_output, "version request generation", 
                                           {"serial_number": serial_number})


@version.command("parse")
@click.argument('telegram_string')
@json_output_option
@handle_service_errors(TelegramParsingError, VersionParsingError)
def parse_version_telegram(telegram_string: str, json_output: bool):
    """
    Parse version information from reply telegram.
    
    Example: xp version parse "<R0020030837F02D02XP230_V1.00.04FI>"
    """
    telegram_service = TelegramService()
    version_service = VersionService()
    formatter = OutputFormatter(json_output)
    
    try:
        # First parse the telegram
        parsed = telegram_service.parse_telegram(telegram_string)
        
        # Check if it's a version-related telegram
        if hasattr(parsed, 'data_value'):  # ReplyTelegram
            result = version_service.parse_version_reply(parsed)
            
            if json_output:
                click.echo(json.dumps(result.to_dict(), indent=2))
            else:
                if result.success:
                    click.echo(version_service.format_version_summary(result.data))
                else:
                    click.echo(f"Error: {result.error}")
                    
        elif hasattr(parsed, 'system_function'):  # SystemTelegram  
            result = version_service.validate_version_telegram(parsed)
            
            if json_output:
                click.echo(json.dumps(result.to_dict(), indent=2))
            else:
                if result.success and result.data['is_version_request']:
                    click.echo(f"Version Request Telegram:")
                    click.echo(f"Serial: {result.data['serial_number']}")
                    click.echo(f"Function: {result.data['function_description']}")
                    click.echo(f"Data Point: {result.data['data_point_description']}")
                else:
                    click.echo(f"Not a version request telegram")
        else:
            error_response = formatter.error_response("Not a version-related telegram", 
                                                    {"raw_input": telegram_string})
            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo("Error: Not a version-related telegram", err=True)
                
    except (TelegramParsingError, VersionParsingError) as e:
        CLIErrorHandler.handle_parsing_error(e, json_output, telegram_string)