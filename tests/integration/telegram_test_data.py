"""Test data fixtures for telegram testing."""

from xp.models import EventType
from xp.models.telegram.event_telegram import EventTelegram

# Valid telegram strings for testing
VALID_TELEGRAMS = [
    "<E14L00I02MAK>",
    "<E14L01I03BB1>",
    "<E5L15I25M00>",
    "<E99L99I90B99>",
    "<E1L00I00MAA>",
    "<E14L00I10MIR>",  # IR remote input
    "<E14L00I89MIR>",  # IR remote input (boundary)
    "<E14L00I90MPS>",  # Proximity sensor
]

# Invalid telegram strings for testing
INVALID_TELEGRAMS = [
    "",
    "E14L00I02MAK>",  # Missing opening bracket
    "<E14L00I02MAK",  # Missing closing bracket
    "<X14L00I02MAK>",  # Wrong prefix
    "<E14X00I02MAK>",  # Invalid link format
    "<E14L00X02MAK>",  # Invalid input format
    "<E14L00I02XAK>",  # Invalid event type
    "<E14L00I02MA>",  # Short checksum
    "<E14L00I02MAKX>",  # Long checksum
    "<E100L00I02MAK>",  # Module type too long
    "<E14L100I02MAK>",  # Link number too long
    "<E14L00I100MAK>",  # Input number too long
    "<E14L00I91MAK>",  # Input number out of range
]

# Test data for multiple telegram parsing
MULTIPLE_TELEGRAM_DATA = [
    {
        "input": "Some data <E14L00I02MAK> more data",
        "expected_count": 1,
        "description": "Single telegram in data stream",
    },
    {
        "input": "Data <E14L00I02MAK> more <E14L01I03BB1> end",
        "expected_count": 2,
        "description": "Two telegrams in data stream",
    },
    {
        "input": "<E14L00I02MAK><E14L01I03BB1><E5L15I25M00>",
        "expected_count": 3,
        "description": "Three consecutive telegrams",
    },
    {
        "input": "No telegrams here at all",
        "expected_count": 0,
        "description": "No telegrams in data stream",
    },
    {
        "input": "Valid <E14L00I02MAK> invalid <INVALID> valid <E14L01I03BB1>",
        "expected_count": 2,
        "description": "Mix of valid and invalid telegrams",
    },
]

# Expected parsed telegram data
EXPECTED_PARSED_DATA = {
    "<E14L00I02MAK>": {
        "module_type": 14,
        "link_number": 0,
        "output_number": 2,
        "event_type": "M",
        "event_type_name": "button_press",
        "input_type": "push_button",
        "checksum": "AK",
    },
    "<E14L01I03BB1>": {
        "module_type": 14,
        "link_number": 1,
        "output_number": 3,
        "event_type": "B",
        "event_type_name": "button_release",
        "input_type": "push_button",
        "checksum": "B1",
    },
    "<E14L00I25MIR>": {
        "module_type": 14,
        "link_number": 0,
        "output_number": 25,
        "event_type": "M",
        "event_type_name": "button_press",
        "input_type": "ir_remote",
        "checksum": "IR",
    },
    "<E14L00I90MPS>": {
        "module_type": 14,
        "link_number": 0,
        "output_number": 90,
        "event_type": "M",
        "event_type_name": "button_press",
        "input_type": "proximity_sensor",
        "checksum": "PS",
    },
}

# CLI command test cases
CLI_TEST_CASES = [
    {
        "command": ["telegram", "parse", "<E14L00I02MAK>"],
        "expected_exit_code": 0,
        "expected_output_contains": ["Module 14", "pressed", "push_button"],
        "description": "Basic telegram parse command",
    },
    {
        "command": ["telegram", "parse", "<E14L00I02MAK>"],
        "expected_exit_code": 0,
        "json_output": True,
        "description": "Telegram parse with JSON output",
    },
    {
        "command": ["telegram", "parse", "INVALID"],
        "expected_exit_code": 1,
        "expected_error": True,
        "description": "Invalid telegram parse command",
    },
    {
        "command": ["telegram", "validate", "<E14L00I02MAK>"],
        "expected_exit_code": 0,
        "expected_output_contains": ["✓ Telegram format is valid"],
        "description": "Telegram validation command",
    },
]


def create_test_telegram(
    module_type=14,
    link_number=0,
    output_number=2,
    event_type=EventType.BUTTON_PRESS,
    checksum="AK",
):
    """Create a test EventTelegram object with specified parameters.

    Args:
        module_type: The module type code.
        link_number: The link number.
        output_number: The output number.
        event_type: The event type.
        checksum: The checksum string.

    Returns:
        EventTelegram: A test EventTelegram object.
    """
    raw_telegram = f"<E{module_type}L{link_number:02d}I{output_number:02d}{event_type.value}{checksum}>"

    return EventTelegram(
        module_type=module_type,
        link_number=link_number,
        input_number=output_number,
        event_type=event_type,
        checksum=checksum,
        raw_telegram=raw_telegram,
    )
