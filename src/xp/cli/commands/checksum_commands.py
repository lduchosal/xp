"""Checksum calculation and validation CLI commands."""
import click
import json

from ...services.checksum_service import ChecksumService
from ..utils.decorators import json_output_option, handle_service_errors
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def checksum():
    """Checksum calculation and validation operations"""
    pass


@checksum.command("calculate")
@click.argument('data')
@click.option('--algorithm', '-a', type=click.Choice(['simple', 'crc32']), 
              default='simple', help='Checksum algorithm to use')
@json_output_option
@handle_service_errors(Exception)
def calculate_checksum(data: str, algorithm: str, json_output: bool):
    """
    Calculate checksum for given data string.
    
    Example: xp checksum calculate "E14L00I02M"
    Example: xp checksum calculate "E14L00I02M" --algorithm crc32
    """
    service = ChecksumService()
    formatter = OutputFormatter(json_output)
    
    try:
        if algorithm == 'simple':
            result = service.calculate_simple_checksum(data)
        else:  # crc32
            result = service.calculate_crc32_checksum(data)
        
        if not result.success:
            error_response = formatter.error_response(result.error, {"input": data})
            click.echo(error_response)
            if json_output:
                raise SystemExit(1)
            else:
                raise click.ClickException("Checksum calculation failed")
        
        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(f"Input: {data}")
            click.echo(f"Algorithm: {result.data['algorithm']}")
            click.echo(f"Checksum: {result.data['checksum']}")
            
    except Exception as e:
        CLIErrorHandler.handle_service_error(e, json_output, "checksum calculation", {"input": data})


@checksum.command("validate")
@click.argument('data')
@click.argument('expected_checksum')
@click.option('--algorithm', '-a', type=click.Choice(['simple', 'crc32']), 
              default='simple', help='Checksum algorithm to use')
@json_output_option
@handle_service_errors(Exception)
def validate_checksum(data: str, expected_checksum: str, algorithm: str, json_output: bool):
    """
    Validate data against expected checksum.
    
    Example: xp checksum validate "E14L00I02M" "AK"
    Example: xp checksum validate "E14L00I02M" "ABCDABCD" --algorithm crc32
    """
    service = ChecksumService()
    formatter = OutputFormatter(json_output)
    
    try:
        if algorithm == 'simple':
            result = service.validate_checksum(data, expected_checksum)
        else:  # crc32
            result = service.validate_crc32_checksum(data, expected_checksum)
        
        if not result.success:
            error_response = formatter.error_response(result.error, {
                "input": data, 
                "expected_checksum": expected_checksum
            })
            click.echo(error_response)
            if json_output:
                raise SystemExit(1)
            else:
                raise click.ClickException("Checksum validation failed")
        
        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(f"Input: {data}")
            click.echo(f"Expected: {expected_checksum}")
            click.echo(f"Calculated: {result.data['calculated_checksum']}")
            status = "✓ Valid" if result.data['is_valid'] else "✗ Invalid"
            click.echo(f"Status: {status}")
            
    except Exception as e:
        CLIErrorHandler.handle_service_error(e, json_output, "checksum validation", {
            "input": data,
            "expected_checksum": expected_checksum
        })