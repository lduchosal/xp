import click
import json
from typing import Dict, Any
from ..services.telegram_service import TelegramService, TelegramParsingError
from ..services.module_type_service import ModuleTypeService, ModuleTypeNotFoundError
from ..services.checksum_service import ChecksumService


@click.group()
@click.version_option()
def cli():
    """XP CLI tool for remote console bus operations"""
    pass


@cli.group()
def telegram():
    """Event telegram operations"""
    pass


@telegram.command("parse-event")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--validate-checksum', '-c', is_flag=True, help='Validate telegram checksum')
def parse_telegram(telegram_string: str, json_output: bool, validate_checksum: bool):
    """
    Parse a single event telegram string.
    
    Example: xp telegram parse "<E14L00I02MAK>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_event_telegram(telegram_string)
        
        # Validate checksum if requested
        checksum_valid = True
        if validate_checksum:
            checksum_valid = service.validate_checksum(parsed)
        
        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output['checksum_valid'] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(service.format_event_telegram_summary(parsed))
            if validate_checksum:
                status = "✓ Valid" if checksum_valid else "✗ Invalid"
                click.echo(f"Checksum validation: {status}")
                
    except TelegramParsingError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "raw_input": telegram_string
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing telegram: {e}", err=True)
            raise click.ClickException("Telegram parsing failed")


@telegram.command("parse-system")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--validate-checksum', '-c', is_flag=True, help='Validate telegram checksum')
def parse_system_telegram(telegram_string: str, json_output: bool, validate_checksum: bool):
    """
    Parse a system telegram string.
    
    Example: xp telegram parse-system "<S0020012521F02D18FN>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_system_telegram(telegram_string)
        
        # Validate checksum if requested
        checksum_valid = True
        if validate_checksum:
            checksum_valid = service.validate_system_checksum(parsed)
        
        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output['checksum_valid'] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(service.format_system_telegram_summary(parsed))
            if validate_checksum:
                status = "✓ Valid" if checksum_valid else "✗ Invalid"
                click.echo(f"Checksum validation: {status}")
                
    except TelegramParsingError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "raw_input": telegram_string
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing system telegram: {e}", err=True)
            raise click.ClickException("System telegram parsing failed")


@telegram.command("parse-reply")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--validate-checksum', '-c', is_flag=True, help='Validate telegram checksum')
def parse_reply_telegram(telegram_string: str, json_output: bool, validate_checksum: bool):
    """
    Parse a reply telegram string.
    
    Example: xp telegram parse-reply "<R0020012521F02D18+26,0§CIL>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_reply_telegram(telegram_string)
        
        # Validate checksum if requested
        checksum_valid = True
        if validate_checksum:
            checksum_valid = service.validate_reply_checksum(parsed)
        
        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output['checksum_valid'] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(service.format_reply_telegram_summary(parsed))
            if validate_checksum:
                status = "✓ Valid" if checksum_valid else "✗ Invalid"
                click.echo(f"Checksum validation: {status}")
                
    except TelegramParsingError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "raw_input": telegram_string
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing reply telegram: {e}", err=True)
            raise click.ClickException("Reply telegram parsing failed")


@telegram.command("parse")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def parse_any_telegram(telegram_string: str, json_output: bool):
    """
    Auto-detect and parse any type of telegram (event, system, or reply).
    
    Example: xp telegram parse "<E14L00I02MAK>"
    Example: xp telegram parse "<S0020012521F02D18FN>"
    Example: xp telegram parse "<R0020012521F02D18+26,0§CIL>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_any_telegram(telegram_string)
        
        if json_output:
            output = parsed.to_dict()
            click.echo(json.dumps(output, indent=2))
        else:
            # Format based on telegram type
            if hasattr(parsed, 'event_type'):  # EventTelegram
                click.echo(service.format_event_telegram_summary(parsed))
            elif hasattr(parsed, 'data_value'):  # ReplyTelegram
                click.echo(service.format_reply_telegram_summary(parsed))
            else:  # SystemTelegram
                click.echo(service.format_system_telegram_summary(parsed))
                
    except TelegramParsingError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "raw_input": telegram_string
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing telegram: {e}", err=True)
            raise click.ClickException("Telegram parsing failed")


@telegram.command("parse-multiple")
@click.argument('data_stream')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def parse_multiple_telegrams(data_stream: str, json_output: bool):
    """
    Parse multiple event telegrams from a data stream.
    
    Example: xp telegram parse-multiple "Some data <E14L00I02MAK> more <E14L01I03BB1>"
    """
    service = TelegramService()
    
    try:
        telegrams = service.parse_multiple_telegrams(data_stream)
        
        if json_output:
            output = {
                "success": True,
                "count": len(telegrams),
                "telegrams": [t.to_dict() for t in telegrams]
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Found {len(telegrams)} telegrams:")
            click.echo("-" * 50)
            for i, telegram in enumerate(telegrams, 1):
                click.echo(f"{i}. {telegram}")
                
    except Exception as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "raw_input": data_stream
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing data stream: {e}", err=True)
            raise click.ClickException("Data stream parsing failed")


@telegram.command("validate")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def validate_telegram(telegram_string: str, json_output: bool):
    """
    Validate the format of an event telegram.
    
    Example: xp telegram validate "<E14L00I02MAK>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_event_telegram(telegram_string)
        checksum_valid = service.validate_checksum(parsed)
        
        if json_output:
            output = {
                "success": True,
                "valid_format": True,
                "valid_checksum": checksum_valid,
                "telegram": parsed.to_dict()
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("✓ Telegram format is valid")
            checksum_status = "✓ Valid" if checksum_valid else "✗ Invalid"
            click.echo(f"Checksum: {checksum_status}")
            click.echo(f"Parsed: {parsed}")
            
    except TelegramParsingError as e:
        if json_output:
            output = {
                "success": False,
                "valid_format": False,
                "error": str(e),
                "raw_input": telegram_string
            }
            click.echo(json.dumps(output, indent=2))
            raise SystemExit(1)
        else:
            click.echo("✗ Telegram format is invalid", err=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Telegram validation failed")


@cli.group()
def module():
    """Module type operations"""
    pass


@module.command("info")
@click.argument('identifier')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def module_info(identifier: str, json_output: bool):
    """
    Get information about a module type by code or name.
    
    Example: xp module info 14
    Example: xp module info XP2606
    """
    service = ModuleTypeService()
    
    try:
        # Try to parse as integer first, then as string
        try:
            module_id = int(identifier)
        except ValueError:
            module_id = identifier
        
        module_type = service.get_module_type(module_id)
        
        if json_output:
            click.echo(json.dumps(module_type.to_dict(), indent=2))
        else:
            click.echo(service.get_module_info_summary(module_id))
            
    except ModuleTypeNotFoundError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "identifier": identifier
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Module type lookup failed")


@module.command("list")
@click.option('--category', '-c', help='Filter by category')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--group-by-category', '-g', is_flag=True, help='Group modules by category')
def module_list(category: str, json_output: bool, group_by_category: bool):
    """
    List module types, optionally filtered by category.
    
    Example: xp module list
    Example: xp module list --category "Interface Panels"
    Example: xp module list --group-by-category
    """
    service = ModuleTypeService()
    
    try:
        if category:
            modules = service.get_modules_by_category(category)
            if not modules:
                if json_output:
                    click.echo(json.dumps({"modules": [], "category": category}))
                else:
                    click.echo(f"No modules found in category '{category}'")
                return
        else:
            modules = service.list_all_modules()
        
        if json_output:
            if group_by_category:
                categories = service.list_modules_by_category()
                output = {
                    "modules_by_category": {
                        cat: [mod.to_dict() for mod in mods] 
                        for cat, mods in categories.items()
                    }
                }
            else:
                output = {
                    "modules": [module.to_dict() for module in modules],
                    "count": len(modules)
                }
            click.echo(json.dumps(output, indent=2))
        else:
            if group_by_category:
                click.echo(service.get_all_modules_summary(group_by_category=True))
            else:
                click.echo(service.get_all_modules_summary(group_by_category=False))
                
    except Exception as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e)
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error listing modules: {e}", err=True)
            raise click.ClickException("Module listing failed")


@module.command("search")
@click.argument('query')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--field', multiple=True, type=click.Choice(['name', 'description']), 
              help='Fields to search in (default: both)')
def module_search(query: str, json_output: bool, field: tuple):
    """
    Search for module types by name or description.
    
    Example: xp module search "push button"
    Example: xp module search --field name "XP"
    """
    service = ModuleTypeService()
    
    try:
        search_fields = list(field) if field else ['name', 'description']
        matching_modules = service.search_modules(query, search_fields)
        
        if json_output:
            output = {
                "query": query,
                "search_fields": search_fields,
                "matches": [module.to_dict() for module in matching_modules],
                "count": len(matching_modules)
            }
            click.echo(json.dumps(output, indent=2))
        else:
            if matching_modules:
                click.echo(f"Found {len(matching_modules)} modules matching '{query}':")
                click.echo("-" * 60)
                for module in matching_modules:
                    click.echo(f"{module.code:2} - {module.name}: {module.description}")
            else:
                click.echo(f"No modules found matching '{query}'")
                
    except Exception as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "query": query
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error searching modules: {e}", err=True)
            raise click.ClickException("Module search failed")


@module.command("categories")
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def module_categories(json_output: bool):
    """
    List all available module categories.
    
    Example: xp module categories
    """
    service = ModuleTypeService()
    
    try:
        categories = service.list_modules_by_category()
        
        if json_output:
            output = {
                "categories": {
                    category: len(modules) 
                    for category, modules in categories.items()
                }
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Available categories:")
            click.echo("-" * 30)
            for category, modules in categories.items():
                click.echo(f"{category}: {len(modules)} modules")
                
    except Exception as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e)
            }
            click.echo(json.dumps(output, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error listing categories: {e}", err=True)
            raise click.ClickException("Category listing failed")


@cli.group()
def checksum():
    """Checksum calculation and validation operations"""
    pass


@checksum.command("calculate")
@click.argument('data')
@click.option('--algorithm', '-a', type=click.Choice(['simple', 'crc32']), 
              default='simple', help='Checksum algorithm to use')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def calculate_checksum(data: str, algorithm: str, json_output: bool):
    """
    Calculate checksum for given data string.
    
    Example: xp checksum calculate "E14L00I02M"
    Example: xp checksum calculate "E14L00I02M" --algorithm crc32
    """
    service = ChecksumService()
    
    try:
        if algorithm == 'simple':
            result = service.calculate_simple_checksum(data)
        else:  # crc32
            result = service.calculate_crc32_checksum(data)
        
        if not result.success:
            if json_output:
                click.echo(json.dumps(result.to_dict(), indent=2))
                raise SystemExit(1)
            else:
                click.echo(f"Error: {result.error}", err=True)
                raise click.ClickException("Checksum calculation failed")
        
        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(f"Input: {data}")
            click.echo(f"Algorithm: {result.data['algorithm']}")
            click.echo(f"Checksum: {result.data['checksum']}")
            
    except Exception as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "input": data
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error calculating checksum: {e}", err=True)
            raise click.ClickException("Checksum calculation failed")


@checksum.command("validate")
@click.argument('data')
@click.argument('expected_checksum')
@click.option('--algorithm', '-a', type=click.Choice(['simple', 'crc32']), 
              default='simple', help='Checksum algorithm to use')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def validate_checksum(data: str, expected_checksum: str, algorithm: str, json_output: bool):
    """
    Validate data against expected checksum.
    
    Example: xp checksum validate "E14L00I02M" "AK"
    Example: xp checksum validate "E14L00I02M" "ABCDABCD" --algorithm crc32
    """
    service = ChecksumService()
    
    try:
        if algorithm == 'simple':
            result = service.validate_checksum(data, expected_checksum)
        else:  # crc32
            result = service.validate_crc32_checksum(data, expected_checksum)
        
        if not result.success:
            if json_output:
                click.echo(json.dumps(result.to_dict(), indent=2))
                raise SystemExit(1)
            else:
                click.echo(f"Error: {result.error}", err=True)
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
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "input": data,
                "expected_checksum": expected_checksum
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error validating checksum: {e}", err=True)
            raise click.ClickException("Checksum validation failed")


if __name__ == '__main__':
    cli()