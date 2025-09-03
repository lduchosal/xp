import click
import json
from typing import Dict, Any
from ..services.telegram_service import TelegramService, TelegramParsingError
from ..services.module_type_service import ModuleTypeService, ModuleTypeNotFoundError
from ..services.checksum_service import ChecksumService
from ..services.link_number_service import LinkNumberService, LinkNumberError
from ..services.discovery_service import DiscoveryService, DiscoveryError, DeviceInfo
from ..services.version_service import VersionService, VersionParsingError
from ..services.conbus_server_service import ConbusServerService, ConbusServerError


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
            checksum_valid = service.validate_checksum(parsed)
        
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
            checksum_valid = service.validate_checksum(parsed)
        
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


@telegram.command("parse-discover-request")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--validate-checksum', '-c', is_flag=True, help='Validate telegram checksum')
def parse_discovery_request_telegram(telegram_string: str, json_output: bool, validate_checksum: bool):
    """
    Parse a discovery request telegram string.
    
    Example: xp telegram parse-discover-request "<S0000000000F01D00FA>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_discovery_request(telegram_string)
        
        # Validate checksum if requested
        checksum_valid = True
        if validate_checksum:
            checksum_valid = service.validate_discovery_request_checksum(parsed)
        
        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output['checksum_valid'] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            broadcast_info = "Broadcast " if parsed.is_broadcast else f"From {parsed.source_address} "
            click.echo(f"Discovery Request: {broadcast_info}Command")
            click.echo(f"Source: {parsed.source_address}")
            click.echo(f"Command: {parsed.command}")
            click.echo(f"Raw: {parsed.raw_telegram}")
            click.echo(f"Timestamp: {parsed.timestamp}")
            click.echo(f"Checksum: {parsed.checksum}")
            
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
            click.echo(f"Error parsing discovery request: {e}", err=True)
            raise click.ClickException("Discovery request parsing failed")


@telegram.command("parse-discover-response")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--validate-checksum', '-c', is_flag=True, help='Validate telegram checksum')
def parse_discovery_response_telegram(telegram_string: str, json_output: bool, validate_checksum: bool):
    """
    Parse a discovery response telegram string.
    
    Example: xp telegram parse-discover-response "<R0020030837F01DFM>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_discovery_response(telegram_string)
        
        # Validate checksum if requested
        checksum_valid = True
        if validate_checksum:
            checksum_valid = service.validate_discovery_response_checksum(parsed)
        
        if json_output:
            output = parsed.to_dict()
            if validate_checksum:
                output['checksum_valid'] = checksum_valid
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Discovery Response: Device {parsed.serial_number} Online")
            click.echo(f"Serial: {parsed.serial_number}")
            click.echo(f"Command: {parsed.full_command}")
            click.echo(f"Raw: {parsed.raw_telegram}")
            click.echo(f"Timestamp: {parsed.timestamp}")
            click.echo(f"Checksum: {parsed.checksum}")
            
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
            click.echo(f"Error parsing discovery response: {e}", err=True)
            raise click.ClickException("Discovery response parsing failed")


@telegram.command("parse")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def parse_telegram(telegram_string: str, json_output: bool):
    """
    Auto-detect and parse any type of telegram (event, system, reply, or discovery).
    
    Example: xp telegram parse "<E14L00I02MAK>"
    Example: xp telegram parse "<S0020012521F02D18FN>"
    Example: xp telegram parse "<R0020012521F02D18+26,0§CIL>"
    Example: xp telegram parse "<S0000000000F01D00FA>"
    Example: xp telegram parse "<R0020030837F01DFM>"
    """
    service = TelegramService()
    
    try:
        parsed = service.parse_telegram(telegram_string)
        
        if json_output:
            output = parsed.to_dict()
            click.echo(json.dumps(output, indent=2))
        else:
            # Format based on telegram type
            if hasattr(parsed, 'event_type'):  # EventTelegram
                click.echo(service.format_event_telegram_summary(parsed))
            elif hasattr(parsed, 'data_value'):  # ReplyTelegram
                click.echo(service.format_reply_telegram_summary(parsed))
            elif hasattr(parsed, 'source_address'):  # DiscoveryRequest
                broadcast_info = "Broadcast " if parsed.is_broadcast else f"From {parsed.source_address} "
                click.echo(f"Discovery Request: {broadcast_info}Command")
                click.echo(f"Raw: {parsed.raw_telegram}")
                click.echo(f"Timestamp: {parsed.timestamp}")
            elif hasattr(parsed, 'device_id'):  # DiscoveryResponse
                click.echo(f"Discovery Response: Device {parsed.serial_number} Online")
                click.echo(f"Raw: {parsed.raw_telegram}")
                click.echo(f"Timestamp: {parsed.timestamp}")
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


@cli.group()
def linknumber():
    """Link number operations for module configuration"""
    pass


@linknumber.command("generate")
@click.argument('serial_number')
@click.argument('link_number', type=int)
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def generate_set_link_number(serial_number: str, link_number: int, json_output: bool):
    """
    Generate a telegram to set module link number.
    
    Example: xp linknumber generate 0020044974 25
    """
    service = LinkNumberService()
    
    try:
        telegram = service.generate_set_link_number_telegram(serial_number, link_number)
        
        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "link_number": link_number,
                "operation": "set_link_number"
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Set Link Number Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Link Number: {link_number}")
            click.echo(f"Telegram: {telegram}")
            
    except LinkNumberError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "serial_number": serial_number,
                "link_number": link_number
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error generating link number telegram: {e}", err=True)
            raise click.ClickException("Link number telegram generation failed")


@linknumber.command("read")
@click.argument('serial_number')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def generate_read_link_number(serial_number: str, json_output: bool):
    """
    Generate a telegram to read module link number.
    
    Example: xp linknumber read 0020044974
    """
    service = LinkNumberService()
    
    try:
        telegram = service.generate_read_link_number_telegram(serial_number)
        
        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "serial_number": serial_number,
                "operation": "read_link_number"
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Read Link Number Telegram:")
            click.echo(f"Serial: {serial_number}")
            click.echo(f"Telegram: {telegram}")
            
    except LinkNumberError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "serial_number": serial_number
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error generating read telegram: {e}", err=True)
            raise click.ClickException("Read telegram generation failed")


@linknumber.command("parse")
@click.argument('telegram_list', nargs=-1, required=True)
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def parse_link_number_telegrams(telegram_list: tuple, json_output: bool):
    """
    Parse link number related telegrams (system and reply).
    
    Example: xp linknumber parse "<S0020044974F04D0425FO>" "<R0020044974F18DFB>"
    Example: xp linknumber parse "<S0020044974F04D0409FA>" "<R0020044974F19DFA>"
    """
    telegram_service = TelegramService()
    link_service = LinkNumberService()
    
    results = []
    
    for telegram_str in telegram_list:
        try:
            # Parse the telegram
            parsed = telegram_service.parse_telegram(telegram_str)
            
            result = {
                "raw_telegram": telegram_str,
                "parsed": parsed.to_dict(),
                "telegram_type": parsed.to_dict().get("telegram_type", "unknown")
            }
            
            # Add specific analysis for reply telegrams
            if hasattr(parsed, 'data_value'):  # ReplyTelegram
                if link_service.is_ack_response(parsed):
                    result["response_type"] = "ACK"
                    result["status"] = "Acknowledged"
                elif link_service.is_nak_response(parsed):
                    result["response_type"] = "NAK"
                    result["status"] = "Not Acknowledged"
                else:
                    # Try to parse link number value
                    link_num = link_service.parse_link_number_from_reply(parsed)
                    if link_num is not None:
                        result["link_number"] = link_num
                        result["status"] = "Link Number Response"
            
            results.append(result)
            
        except (TelegramParsingError, LinkNumberError) as e:
            error_result = {
                "raw_telegram": telegram_str,
                "error": str(e),
                "success": False
            }
            results.append(error_result)
    
    if json_output:
        output = {
            "results": results,
            "count": len(results),
            "success": all("error" not in r for r in results)
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"=== Link Number Telegram Analysis ===")
        click.echo(f"Parsed {len(results)} telegrams:")
        click.echo("-" * 60)
        
        for i, result in enumerate(results, 1):
            click.echo(f"{i}. {result['raw_telegram']}")
            
            if "error" in result:
                click.echo(f"   ✗ Error: {result['error']}")
            else:
                telegram_type = result["telegram_type"].capitalize()
                click.echo(f"   ✓ Type: {telegram_type}")
                
                if "response_type" in result:
                    click.echo(f"   → {result['response_type']}: {result['status']}")
                elif "link_number" in result:
                    click.echo(f"   → Link Number: {result['link_number']}")
                elif "parsed" in result:
                    parsed_info = result["parsed"]
                    if "system_function" in parsed_info:
                        func_desc = parsed_info["system_function"]["description"]
                        data_desc = parsed_info["data_point_id"]["description"]
                        click.echo(f"   → Function: {func_desc} for {data_desc}")
            
            click.echo()


@cli.group()
def version():
    """Version information operations for device firmware"""
    pass


@version.command("request")
@click.argument('serial_number')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def generate_version_request(serial_number: str, json_output: bool):
    """
    Generate a telegram to request version information from a device.
    
    Example: xp version request 0020030837
    """
    service = VersionService()
    
    try:
        result = service.generate_version_request_telegram(serial_number)
        
        if not result.success:
            if json_output:
                click.echo(json.dumps(result.to_dict(), indent=2))
                raise SystemExit(1)
            else:
                click.echo(f"Error: {result.error}", err=True)
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
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "serial_number": serial_number
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error generating version request: {e}", err=True)
            raise click.ClickException("Version request generation failed")


@version.command("parse")
@click.argument('telegram_string')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def parse_version_telegram(telegram_string: str, json_output: bool):
    """
    Parse version information from reply telegram.
    
    Example: xp version parse "<R0020030837F02D02XP230_V1.00.04FI>"
    """
    telegram_service = TelegramService()
    version_service = VersionService()
    
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
            if json_output:
                error_response = {
                    "success": False,
                    "error": "Not a version-related telegram",
                    "raw_input": telegram_string
                }
                click.echo(json.dumps(error_response, indent=2))
                raise SystemExit(1)
            else:
                click.echo("Error: Not a version-related telegram", err=True)
                
    except (TelegramParsingError, VersionParsingError) as e:
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


@cli.group()
def discovery():
    """Device discovery operations for console bus enumeration"""
    pass


@discovery.command("generate")
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def generate_discovery(json_output: bool):
    """
    Generate a discovery telegram for device enumeration.
    
    Example: xp discovery generate
    """
    service = DiscoveryService()
    
    try:
        telegram = service.generate_discovery_telegram()
        
        if json_output:
            output = {
                "success": True,
                "telegram": telegram,
                "operation": "discovery_broadcast",
                "broadcast_address": "0000000000"
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Discovery Broadcast Telegram:")
            click.echo(f"Broadcast Address: 0000000000")
            click.echo(f"Telegram: {telegram}")
            click.echo(f"\nUse this telegram to enumerate all devices on the console bus.")
            
    except DiscoveryError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e)
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error generating discovery telegram: {e}", err=True)
            raise click.ClickException("Discovery telegram generation failed")


@discovery.command("parse")
@click.argument('telegram_list', nargs=-1, required=True)
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--summary', is_flag=True, help='Show summary only')
def parse_discovery_responses(telegram_list: tuple, json_output: bool, summary: bool):
    """
    Parse discovery response telegrams to identify discovered devices.
    
    Example: xp discovery parse "<R0020030837F01DFM>" "<R0020044966F01DFK>"
    Example: xp discovery parse --summary "<R0020030837F01DFM>" "<R0020044966F01DFK>"
    """
    telegram_service = TelegramService()
    discovery_service = DiscoveryService()
    
    devices = []
    errors = []
    
    for telegram_str in telegram_list:
        try:
            # Parse the telegram
            if telegram_str.startswith('<R'):
                parsed = telegram_service.parse_reply_telegram(telegram_str)
                device_info = discovery_service.parse_discovery_response(parsed)
                
                if device_info:
                    devices.append(device_info)
                else:
                    errors.append({
                        "telegram": telegram_str,
                        "error": "Not a discovery response telegram"
                    })
            elif telegram_str.startswith('<S'):
                # Handle discovery request telegram
                parsed = telegram_service.parse_system_telegram(telegram_str)
                if parsed.system_function.value == "01":  # Discovery
                    if json_output or not summary:
                        pass  # Will be handled in output
                else:
                    errors.append({
                        "telegram": telegram_str,
                        "error": "Not a discovery telegram"
                    })
            else:
                errors.append({
                    "telegram": telegram_str,
                    "error": "Invalid telegram format"
                })
                
        except (TelegramParsingError, DiscoveryError) as e:
            errors.append({
                "telegram": telegram_str,
                "error": str(e)
            })
    
    if json_output:
        output = {
            "devices": [device.to_dict() for device in devices],
            "summary": discovery_service.generate_discovery_summary(devices),
            "errors": errors,
            "success": len(devices) > 0
        }
        click.echo(json.dumps(output, indent=2))
    else:
        if summary:
            if devices:
                click.echo(discovery_service.format_discovery_results(devices))
            else:
                click.echo("No devices discovered")
        else:
            # Detailed output
            click.echo(f"=== Discovery Response Analysis ===")
            click.echo(f"Processed {len(telegram_list)} telegram(s)")
            
            if devices:
                click.echo(f"\nDiscovered Devices:")
                click.echo("-" * 50)
                
                for i, device in enumerate(devices, 1):
                    status = "✓" if device.checksum_valid else "✗"
                    click.echo(f"{i}. {device.serial_number} ({status})")
                    click.echo(f"   Raw: {device.raw_telegram}")
            
            if errors:
                click.echo(f"\nErrors:")
                click.echo("-" * 50)
                for error in errors:
                    click.echo(f"✗ {error['telegram']}: {error['error']}")
            
            if devices:
                click.echo(f"\n{discovery_service.format_discovery_results(devices)}")


@discovery.command("analyze")
@click.argument('log_file_path')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--time-range', help='Filter by time range (HH:MM:SS,mmm-HH:MM:SS,mmm)')
def analyze_discovery_session(log_file_path: str, json_output: bool, time_range: str):
    """
    Analyze a console bus log file for discovery sessions.
    
    Example: xp discovery analyze conbus-discover.log
    Example: xp discovery analyze conbus.log --time-range "22:48:38,000-22:48:39,000"
    """
    from ..services.log_file_service import LogFileService, LogFileParsingError
    from ..utils.time_utils import parse_time_range, TimeParsingError
    
    log_service = LogFileService()
    telegram_service = TelegramService()
    discovery_service = DiscoveryService()
    
    try:
        # Parse the log file
        entries = log_service.parse_log_file(log_file_path)
        
        # Apply time filter if specified
        if time_range:
            try:
                start_time, end_time = parse_time_range(time_range)
                entries = log_service.filter_entries(entries, start_time=start_time, end_time=end_time)
            except TimeParsingError as e:
                if json_output:
                    error_response = {"success": False, "error": f"Invalid time range: {e}"}
                    click.echo(json.dumps(error_response, indent=2))
                    raise SystemExit(1)
                else:
                    click.echo(f"Error: Invalid time range: {e}", err=True)
                    raise click.ClickException("Invalid time range format")
        
        # Find discovery sessions
        discovery_requests = []
        discovery_responses = []
        
        for entry in entries:
            if entry.parsed_telegram and entry.parse_error is None:
                # Check for discovery system telegrams (requests)
                if hasattr(entry.parsed_telegram, 'system_function') and not hasattr(entry.parsed_telegram, 'data_value'):
                    if entry.parsed_telegram.system_function.value == "01":  # Discovery
                        discovery_requests.append(entry)
                
                # Check for discovery reply telegrams (responses)
                elif hasattr(entry.parsed_telegram, 'data_value'):
                    if discovery_service.is_discovery_response(entry.parsed_telegram):
                        discovery_responses.append(entry)
        
        # Extract device information
        devices = []
        for response_entry in discovery_responses:
            device_info = discovery_service.parse_discovery_response(response_entry.parsed_telegram)
            if device_info:
                devices.append(device_info)
        
        summary = discovery_service.generate_discovery_summary(devices)
        
        if json_output:
            output = {
                "file_path": log_file_path,
                "discovery_requests": len(discovery_requests),
                "discovery_responses": len(discovery_responses),
                "devices": [device.to_dict() for device in devices],
                "summary": summary,
                "success": len(devices) > 0
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"=== Discovery Session Analysis ===")
            click.echo(f"File: {log_file_path}")
            
            if time_range:
                click.echo(f"Time Range: {time_range}")
            
            click.echo(f"Discovery Requests: {len(discovery_requests)}")
            click.echo(f"Discovery Responses: {len(discovery_responses)}")
            
            if discovery_requests:
                click.echo(f"\nDiscovery Requests:")
                for req in discovery_requests[:3]:  # Show first 3
                    click.echo(f"  {req.timestamp.strftime('%H:%M:%S,%f')[:-3]} [{req.direction}] {req.raw_telegram}")
                if len(discovery_requests) > 3:
                    click.echo(f"  ... and {len(discovery_requests) - 3} more")
            
            if devices:
                click.echo(f"\n{discovery_service.format_discovery_results(devices)}")
            else:
                click.echo(f"\nNo devices discovered in the log file.")
                
    except LogFileParsingError as e:
        if json_output:
            error_response = {"success": False, "error": str(e), "file_path": log_file_path}
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error analyzing log file: {e}", err=True)
            raise click.ClickException("Log file analysis failed")


# File operations command group
@cli.group()
def file():
    """File operations for console bus logs"""
    pass


@file.command("decode")
@click.argument('log_file_path')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
@click.option('--filter-type', type=click.Choice(['event', 'system', 'reply']), help='Filter by telegram type')
@click.option('--filter-direction', type=click.Choice(['tx', 'rx']), help='Filter by direction')
@click.option('--time-range', help='Filter by time range (HH:MM:SS,mmm-HH:MM:SS,mmm)')
@click.option('--summary', is_flag=True, help='Show summary statistics only')
def decode_log_file(log_file_path: str, json_output: bool, filter_type: str, 
                   filter_direction: str, time_range: str, summary: bool):
    """
    Decode and parse console bus log file.
    
    Example: xp file decode conbus.log
    Example: xp file decode conbus.log --filter-type event --json-output
    """
    from ..services.log_file_service import LogFileService, LogFileParsingError
    from ..utils.time_utils import parse_time_range, TimeParsingError
    
    service = LogFileService()
    
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
                    if json_output:
                        error_response = {"success": False, "error": f"Invalid time range: {e}"}
                        click.echo(json.dumps(error_response, indent=2))
                        raise SystemExit(1)
                    else:
                        click.echo(f"Error: Invalid time range: {e}", err=True)
                        raise click.ClickException("Invalid time range format")
            
            entries = service.filter_entries(
                entries, 
                telegram_type=filter_type,
                direction=filter_direction,
                start_time=start_time,
                end_time=end_time
            )
        
        # Generate statistics
        stats = service.get_file_statistics(entries)
        
        if summary:
            # Show summary only
            if json_output:
                click.echo(json.dumps({"statistics": stats, "entry_count": len(entries)}, indent=2))
            else:
                _format_summary_output(log_file_path, stats, len(entries))
        else:
            # Show full results
            if json_output:
                output = {
                    "file_path": log_file_path,
                    "statistics": stats,
                    "entries": [entry.to_dict() for entry in entries]
                }
                click.echo(json.dumps(output, indent=2))
            else:
                _format_decode_output(log_file_path, entries, stats)
                
    except LogFileParsingError as e:
        if json_output:
            error_response = {"success": False, "error": str(e), "file_path": log_file_path}
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing log file: {e}", err=True)
            raise click.ClickException("Log file parsing failed")


@file.command("analyze")
@click.argument('log_file_path')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def analyze_log_file(log_file_path: str, json_output: bool):
    """
    Analyze console bus log file for patterns and statistics.
    
    Example: xp file analyze conbus.log
    """
    from ..services.log_file_service import LogFileService, LogFileParsingError
    
    service = LogFileService()
    
    try:
        entries = service.parse_log_file(log_file_path)
        stats = service.get_file_statistics(entries)
        
        if json_output:
            click.echo(json.dumps({"file_path": log_file_path, "analysis": stats}, indent=2))
        else:
            _format_analysis_output(log_file_path, stats)
            
    except LogFileParsingError as e:
        if json_output:
            error_response = {"success": False, "error": str(e), "file_path": log_file_path}
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error analyzing log file: {e}", err=True)
            raise click.ClickException("Log file analysis failed")


@file.command("validate")
@click.argument('log_file_path')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def validate_log_file(log_file_path: str, json_output: bool):
    """
    Validate console bus log file format and telegram checksums.
    
    Example: xp file validate conbus.log
    """
    from ..services.log_file_service import LogFileService, LogFileParsingError
    
    service = LogFileService()
    
    try:
        entries = service.parse_log_file(log_file_path)
        stats = service.get_file_statistics(entries)
        
        is_valid = stats['parse_errors'] == 0
        checksum_issues = stats['checksum_validation']['invalid_checksums']
        
        if json_output:
            result = {
                "file_path": log_file_path,
                "valid_format": is_valid,
                "parse_errors": stats['parse_errors'],
                "checksum_issues": checksum_issues,
                "statistics": stats,
                "success": is_valid and checksum_issues == 0
            }
            click.echo(json.dumps(result, indent=2))
        else:
            _format_validation_output(log_file_path, entries, stats, is_valid)
            
    except LogFileParsingError as e:
        if json_output:
            error_response = {"success": False, "error": str(e), "file_path": log_file_path}
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error validating log file: {e}", err=True)
            raise click.ClickException("Log file validation failed")


def _format_summary_output(file_path: str, stats: dict, entry_count: int):
    """Format summary output for human reading"""
    click.echo(f"=== Console Bus Log Summary ===")
    click.echo(f"File: {file_path}")
    click.echo(f"Entries: {entry_count}")
    
    if stats.get('time_range', {}).get('start'):
        click.echo(f"Time Range: {stats['time_range']['start']} - {stats['time_range']['end']}")
        click.echo(f"Duration: {stats['time_range']['duration_seconds']:.3f} seconds")
    
    click.echo(f"\nTelegram Distribution:")
    type_counts = stats.get('telegram_type_counts', {})
    for t_type, count in type_counts.items():
        percentage = (count / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
        click.echo(f"  {t_type.capitalize()}: {count} ({percentage:.1f}%)")
    
    click.echo(f"\nDirection Distribution:")
    dir_counts = stats.get('direction_counts', {})
    for direction, count in dir_counts.items():
        percentage = (count / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
        click.echo(f"  {direction.upper()}: {count} ({percentage:.1f}%)")


def _format_decode_output(file_path: str, entries: list, stats: dict):
    """Format decode output for human reading"""
    _format_summary_output(file_path, stats, len(entries))
    
    click.echo(f"\n=== Log Entries ===")
    for entry in entries:
        click.echo(str(entry))


def _format_analysis_output(file_path: str, stats: dict):
    """Format analysis output for human reading"""
    click.echo(f"=== Console Bus Log Analysis ===")
    click.echo(f"File: {file_path}")
    
    if stats.get('time_range', {}).get('start'):
        click.echo(f"Time Range: {stats['time_range']['start']} - {stats['time_range']['end']}")
        click.echo(f"Duration: {stats['time_range']['duration_seconds']:.3f} seconds")
    
    click.echo(f"\nParsing Results:")
    click.echo(f"  Total Entries: {stats['total_entries']}")
    click.echo(f"  Successfully Parsed: {stats['valid_parses']}")
    click.echo(f"  Parse Errors: {stats['parse_errors']}")
    click.echo(f"  Parse Success Rate: {stats['parse_success_rate']:.1f}%")
    
    click.echo(f"\nChecksum Validation:")
    cv = stats['checksum_validation']
    click.echo(f"  Validated Telegrams: {cv['validated_count']}")
    click.echo(f"  Valid Checksums: {cv['valid_checksums']}")
    click.echo(f"  Invalid Checksums: {cv['invalid_checksums']}")
    click.echo(f"  Validation Success Rate: {cv['validation_success_rate']:.1f}%")
    
    click.echo(f"\nTelegram Types:")
    type_counts = stats['telegram_type_counts']
    for t_type, count in type_counts.items():
        percentage = (count / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
        click.echo(f"  {t_type.capitalize()}: {count} ({percentage:.1f}%)")
    
    click.echo(f"\nDirection Distribution:")
    dir_counts = stats['direction_counts']
    for direction, count in dir_counts.items():
        percentage = (count / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
        click.echo(f"  {direction.upper()}: {count} ({percentage:.1f}%)")
    
    if stats.get('devices'):
        click.echo(f"\nDevices Found:")
        for device in stats['devices']:
            click.echo(f"  {device}")


def _format_validation_output(file_path: str, entries: list, stats: dict, is_valid: bool):
    """Format validation output for human reading"""
    click.echo(f"=== Console Bus Log Validation ===")
    click.echo(f"File: {file_path}")
    
    status = "✓ VALID" if is_valid else "✗ INVALID"
    click.echo(f"Format Status: {status}")
    
    if stats['parse_errors'] > 0:
        click.echo(f"\nParse Errors Found: {stats['parse_errors']}")
        error_entries = [e for e in entries if e.parse_error]
        for entry in error_entries[:5]:  # Show first 5 errors
            click.echo(f"  Line {entry.line_number}: {entry.parse_error}")
        
        if len(error_entries) > 5:
            click.echo(f"  ... and {len(error_entries) - 5} more errors")
    
    cv = stats['checksum_validation']
    if cv['invalid_checksums'] > 0:
        click.echo(f"\nChecksum Issues: {cv['invalid_checksums']} invalid checksums found")
        invalid_entries = [e for e in entries if e.checksum_validated is False]
        for entry in invalid_entries[:5]:  # Show first 5 checksum errors
            click.echo(f"  Line {entry.line_number}: {entry.raw_telegram}")
        
        if len(invalid_entries) > 5:
            click.echo(f"  ... and {len(invalid_entries) - 5} more checksum errors")
    
    if is_valid and cv['invalid_checksums'] == 0:
        click.echo(f"\n✓ All telegrams parsed successfully")
        click.echo(f"✓ All checksums validated successfully")


@cli.group()
def server():
    """Conbus emulator server operations"""
    pass


# Global server instance
_server_instance = None


@server.command("start")
@click.option('--port', '-p', default=10001, type=int, help='Port to listen on (default: 10001)')
@click.option('--config', '-c', default="config.yml", help='Configuration file path')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def start_server(port: int, config: str, json_output: bool):
    """
    Start the Conbus emulator server.
    
    Example: xp server start
    Example: xp server start --port 1001 --config my_config.yml
    """
    global _server_instance
    
    try:
        # Check if server is already running
        if _server_instance and _server_instance.is_running:
            if json_output:
                error_response = {
                    "success": False,
                    "error": "Server is already running"
                }
                click.echo(json.dumps(error_response, indent=2))
                raise SystemExit(1)
            else:
                click.echo("Error: Server is already running", err=True)
                raise click.ClickException("Server already running")
        
        # Create and start server
        _server_instance = ConbusServerService(config_path=config, port=port)
        
        if json_output:
            status = _server_instance.get_server_status()
            click.echo(json.dumps(status, indent=2))
        else:
            click.echo(f"Starting Conbus emulator server...")
            click.echo(f"Port: {port}")
            click.echo(f"Config: {config}")
            
        # This will block until server is stopped
        _server_instance.start_server()
        
    except ConbusServerError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "port": port,
                "config": config
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error starting server: {e}", err=True)
            raise click.ClickException("Server startup failed")
    except KeyboardInterrupt:
        if json_output:
            shutdown_response = {
                "success": True,
                "message": "Server shutdown by user"
            }
            click.echo(json.dumps(shutdown_response, indent=2))
        else:
            click.echo(f"\nServer shutdown by user")


@server.command("stop")
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def stop_server(json_output: bool):
    """
    Stop the running Conbus emulator server.
    
    Example: xp server stop
    """
    global _server_instance
    
    try:
        if _server_instance is None or not _server_instance.is_running:
            if json_output:
                error_response = {
                    "success": False,
                    "error": "No server is currently running"
                }
                click.echo(json.dumps(error_response, indent=2))
                raise SystemExit(1)
            else:
                click.echo("No server is currently running", err=True)
                raise click.ClickException("No server running")
        
        # Stop the server
        _server_instance.stop_server()
        
        if json_output:
            response = {
                "success": True,
                "message": "Server stopped successfully"
            }
            click.echo(json.dumps(response, indent=2))
        else:
            click.echo("Server stopped successfully")
            
    except ConbusServerError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e)
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error stopping server: {e}", err=True)
            raise click.ClickException("Server stop failed")


@server.command("status")
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def server_status(json_output: bool):
    """
    Get status of the Conbus emulator server.
    
    Example: xp server status
    """
    global _server_instance
    
    try:
        if _server_instance is None:
            status = {
                "running": False,
                "port": None,
                "devices_configured": 0,
                "device_list": []
            }
        else:
            status = _server_instance.get_server_status()
        
        if json_output:
            click.echo(json.dumps(status, indent=2))
        else:
            if status["running"]:
                click.echo("✓ Server is running")
                click.echo(f"  Port: {status['port']}")
                click.echo(f"  Devices configured: {status['devices_configured']}")
                if status['device_list']:
                    click.echo(f"  Device list: {', '.join(status['device_list'])}")
            else:
                click.echo("✗ Server is not running")
                
    except Exception as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e)
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Error getting server status: {e}", err=True)
            raise click.ClickException("Status check failed")


if __name__ == '__main__':
    cli()