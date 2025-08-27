import re
from functools import wraps
import click


def validate_telegram_format(f):
    """
    Decorator to validate telegram format before processing.
    Follows the architecture requirement for input validation.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Get the telegram_string argument
        telegram_string = None
        if args:
            telegram_string = args[0] if len(args) > 0 else None
        if not telegram_string and 'telegram_string' in kwargs:
            telegram_string = kwargs['telegram_string']
        
        if telegram_string:
            if not validate_telegram_string(telegram_string):
                raise click.BadParameter(
                    f"Invalid telegram format: {telegram_string}. "
                    f"Expected format: <E{{module}}L{{link}}I{{input}}{{M|B}}{{checksum}}>"
                )
        
        return f(*args, **kwargs)
    return wrapper


def validate_telegram_string(telegram: str) -> bool:
    """
    Validate basic telegram string format.
    
    Args:
        telegram: The telegram string to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    if not telegram:
        return False
    
    # Basic format check
    pattern = r'^<E\d{1,2}L\d{2}I\d{2}[MB][A-Z0-9]{2}>$'
    return bool(re.match(pattern, telegram.strip()))


def validate_input_range(value: int, min_val: int, max_val: int, field_name: str) -> None:
    """
    Validate that an integer value is within the specified range.
    
    Args:
        value: The value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages
        
    Raises:
        click.BadParameter: If value is out of range
    """
    if not (min_val <= value <= max_val):
        raise click.BadParameter(
            f"{field_name} must be between {min_val} and {max_val}, got {value}"
        )


def validate_data_stream(data: str) -> bool:
    """
    Validate that a data stream contains at least one valid telegram.
    
    Args:
        data: The data stream to validate
        
    Returns:
        True if at least one telegram is found, False otherwise
    """
    if not data:
        return False
    
    # Look for telegram patterns
    pattern = r'<E\d{1,2}L\d{2}I\d{2}[MB][A-Z0-9]{2}>'
    return bool(re.search(pattern, data))


class TelegramValidator:
    """
    Validator class for comprehensive telegram validation.
    Follows the architecture pattern for structured validation.
    """
    
    @staticmethod
    def validate_module_type(module_type: int) -> None:
        """Validate module type range"""
        validate_input_range(module_type, 1, 99, "Module type")
    
    @staticmethod
    def validate_link_number(link_number: int) -> None:
        """Validate link number range"""
        validate_input_range(link_number, 0, 99, "Link number")
    
    @staticmethod
    def validate_input_number(input_number: int) -> None:
        """Validate input number range"""
        validate_input_range(input_number, 0, 90, "Input number")
    
    @staticmethod
    def validate_event_type(event_type: str) -> None:
        """Validate event type"""
        if event_type not in ['M', 'B']:
            raise click.BadParameter(f"Event type must be 'M' or 'B', got '{event_type}'")
    
    @staticmethod
    def validate_checksum(checksum: str) -> None:
        """Validate checksum format"""
        if not checksum or len(checksum) != 2:
            raise click.BadParameter("Checksum must be exactly 2 characters")
        
        if not checksum.isalnum():
            raise click.BadParameter("Checksum must contain only alphanumeric characters")