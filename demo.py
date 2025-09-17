#!/usr/bin/env python3
"""
Demo script showing XP System functionality including:
- Telegram Event parsing (Feature-Telegram-Event.md)
- Version parsing (Feature-Parse-Version.md)
- Module type information and classification
- System and Reply telegram handling
- Comprehensive error handling and edge cases

This demonstrates the complete implemented XP console bus protocol.
"""

import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from xp.services.telegram_service import TelegramService, TelegramParsingError
from xp.services.module_type_service import ModuleTypeService
from xp.services.telegram_version_service import VersionService
from xp.models.datapoint_type import DataPointType


def demo_basic_parsing():
    """Demonstrate basic telegram parsing"""
    print("=== Basic Telegram Parsing Demo ===\n")

    service = TelegramService()
    test_telegrams = [
        "<E14L00I02MAK>",  # Button press
        "<E14L01I03BB1>",  # Button release
        "<E14L00I25MIR>",  # IR remote
        "<E14L00I90MPS>",  # Proximity sensor
    ]

    for telegram_str in test_telegrams:
        try:
            telegram = service.parse_telegram(telegram_str)
            print(f"Raw: {telegram.raw_telegram}")
            print(f"Parsed: {telegram}")
            print(f"Type: {telegram.input_type.value}")
            print(f"Action: {'pressed' if telegram.is_button_press else 'released'}")
            print(f"Checksum: {telegram.checksum}")
            print("-" * 50)
        except TelegramParsingError as e:
            print(f"Error parsing {telegram_str}: {e}")
            print("-" * 50)

def demo_validation():
    """Demonstrate telegram validation"""
    print("\n=== Telegram Validation Demo ===\n")

    service = TelegramService()
    test_cases = [
        ("<E14L00I02MAK>", "Valid telegram"),
        ("E14L00I02MAK>", "Missing opening bracket"),
        ("<E14L00I02MAK", "Missing closing bracket"),
        ("<X14L00I02MAK>", "Wrong prefix"),
        ("<E14L00I91MAK>", "Input out of range"),
    ]

    for telegram_str, description in test_cases:
        try:
            telegram = service.parse_telegram(telegram_str)
            checksum_valid = service.validate_checksum(telegram)
            status = "✓ VALID" if checksum_valid else "⚠ FORMAT OK, CHECKSUM INVALID"
            print(f"{status:25} | {description:25} | {telegram_str}")
        except TelegramParsingError:
            print(f"{'✗ INVALID':25} | {description:25} | {telegram_str}")


def demo_input_types():
    """Demonstrate different input types"""
    print("\n=== Input Type Classification Demo ===\n")

    service = TelegramService()
    input_examples = [
        ("<E14L00I00MAK>", "Push button (0-9)"),
        ("<E14L00I09MAK>", "Push button (0-9)"),
        ("<E14L00I10MIR>", "IR remote (10-89)"),
        ("<E14L00I45MIR>", "IR remote (10-89)"),
        ("<E14L00I89MIR>", "IR remote (10-89)"),
        ("<E14L00I90MPS>", "Proximity sensor (90)"),
    ]

    print(f"{'Input #':<8} | {'Type':<16} | {'Description':<20} | {'Raw Telegram'}")
    print("-" * 65)

    for telegram_str, description in input_examples:
        try:
            telegram = service.parse_telegram(telegram_str)
            print(
                f"{telegram.input_number:<8} | {telegram.input_type.value:<16} | {description:<20} | {telegram_str}"
            )
        except TelegramParsingError:
            print(f"{'ERROR':<8} | {'N/A':<16} | {description:<20} | {telegram_str}")


def demo_module_types():
    """Demonstrate module type functionality"""
    print("\n=== Module Type Functionality Demo ===\n")

    service = ModuleTypeService()

    print("1. Module Type Lookup:")
    print("-" * 25)

    # Demonstrate lookup by code and name
    test_cases = [(14, "XP2606"), (7, "XP24"), (3, "CP70A"), (22, "XPX1_8")]

    for code, expected_name in test_cases:
        module = service.get_module_type(code)
        print(f"Code {code:2}: {module.name} - {module.description}")
        print(f"         Category: {module.category}")
        features = []
        if module.is_push_button_panel:
            features.append("Push Button Panel")
        if module.is_ir_capable:
            features.append("IR Capable")
        if module.is_reserved:
            features.append("Reserved")
        if features:
            print(f"         Features: {', '.join(features)}")
        print()

    print("2. Search Functionality:")
    print("-" * 22)

    # Search for push button panels
    panels = service.search_modules("push button")
    print(f"Found {len(panels)} push button panels:")
    for panel in panels[:3]:  # Show first 3
        print(f"  - {panel.name}: {panel.description}")
    print()

    # Search for IR capable modules
    ir_modules = service.get_ir_capable_modules()
    print(f"Found {len(ir_modules)} IR-capable modules:")
    for module in ir_modules[:3]:  # Show first 3
        print(f"  - {module.name}: {module.description}")
    print()

    print("3. Categories:")
    print("-" * 12)
    categories = service.list_modules_by_category()
    for category, modules in categories.items():
        print(f"{category}: {len(modules)} modules")
        # Show first module in each category
        if modules:
            print(f"  Examples: {modules[0].name}")
    print()


def demo_enhanced_telegram_parsing():
    """Demonstrate enhanced telegram parsing with module information"""
    print("\n=== Enhanced Telegram Parsing Demo ===\n")

    telegram_service = TelegramService()

    # Test telegrams with different module types
    test_telegrams = [
        "<E14L00I02MAK>",  # XP2606 - Push button panel
        "<E7L01I01MR1>",  # XP24 - Relay module
        "<E3L00I15MIR>",  # CP70A - IR link module
        "<E22L00I07MAK>",  # XPX1_8 - 8-way push button panel
    ]

    print("Enhanced telegram parsing (now includes module information):")
    print("-" * 65)

    for telegram_str in test_telegrams:
        try:
            telegram = telegram_service.parse_telegram(telegram_str)
            print(f"Raw: {telegram.raw_telegram}")
            print(f"Parsed: {telegram}")  # Now includes module name!

            if telegram.module_info:
                print(
                    f"Module: {telegram.module_info.name} - {telegram.module_info.description}"
                )
                print(f"Category: {telegram.module_info.category}")
            else:
                print("Module: Unknown module type")

            print(f"Input Type: {telegram.input_type.value}")
            print("-" * 65)

        except TelegramParsingError as e:
            print(f"Error parsing {telegram_str}: {e}")
            print("-" * 65)


def demo_version_parsing():
    """Demonstrate version telegram parsing functionality"""
    print("\n=== Version Parsing Demo ===\n")

    telegram_service = TelegramService()
    version_service = VersionService()

    print("1. Version Request Generation:")
    print("-" * 32)

    # Generate version request telegrams
    serial_numbers = ["0020030837", "0020044966", "0020041824"]

    for serial in serial_numbers:
        result = version_service.generate_version_request_telegram(serial)
        if result.success:
            print(f"Device {serial}: {result.data['telegram']}")
        else:
            print(f"Error generating request for {serial}: {result.error}")

    print("\n2. System Telegram Parsing (Version Requests):")
    print("-" * 48)

    # Parse version request telegram from specification
    version_system_telegram = "<S0020030837F02D02FM>"

    try:
        parsed = telegram_service.parse_system_telegram(version_system_telegram)
        print(f"Raw: {parsed.raw_telegram}")
        print(f"Serial: {parsed.serial_number}")
        print(f"Function: {parsed.function_description}")
        print(f"Data Point: {parsed.data_point_description}")
        print(
            f"Checksum: {parsed.checksum} {'✓' if parsed.checksum_validated else '✗'}"
        )

        # Validate it's a version request
        validation = version_service.validate_version_telegram(parsed)
        if validation.success and validation.data["is_version_request"]:
            print("✓ Confirmed: This is a version request telegram")
        print()
    except TelegramParsingError as e:
        print(f"Error parsing system telegram: {e}")

    print("3. Version Reply Parsing (From Specification Examples):")
    print("-" * 58)

    # Version reply telegrams from the specification
    version_replies = [
        "<R0020030837F02D02XP230_V1.00.04FI>",
        "<R0020037487F02D02XP20_V0.01.05GK>",
        "<R0020042796F02D02XP33LR_V0.04.02HF>",
        "<R0020044991F02D02XP24_V0.34.03GA>",
        "<R0020044964F02D02XP24_V0.34.03GK>",
        "<R0020041824F02D02XP20_V0.01.05GO>",
    ]

    for telegram_str in version_replies[:4]:  # Show first 4 examples
        try:
            parsed = telegram_service.parse_reply_telegram(telegram_str)
            version_data = parsed.parsed_value

            if version_data["parsed"]:
                print(f"Device {parsed.serial_number}:")
                print(f"  Product: {version_data['product']}")
                print(f"  Version: {version_data['version']}")
                print(f"  Formatted: {version_data['formatted']}")
                print(f"  Raw: {telegram_str}")
                print()
            else:
                print(f"Failed to parse version from: {telegram_str}")

        except TelegramParsingError as e:
            print(f"Error parsing: {telegram_str} - {e}")

    print("4. Auto-Detection via Generic Parse:")
    print("-" * 36)

    # Test auto-detection of version telegrams
    mixed_telegrams = [
        "<S0020030837F02D02FM>",  # Version request
        "<R0020030837F02D02XP230_V1.00.04FI>",  # Version reply
        "<E14L00I02MAK>",  # Event telegram
        "<R0020030837F02D18+26.0§CIL>",  # Temperature reply
    ]

    for telegram_str in mixed_telegrams:
        try:
            parsed = telegram_service.parse_telegram(telegram_str)

            # Determine telegram type based on attributes
            if hasattr(parsed, "event_type"):  # EventTelegram
                telegram_type = "event"
                print(f"Auto-detected: {telegram_type.upper()}")
                print(
                    f"  → {parsed.input_type.value} {parsed.event_type.value} from module {parsed.module_type}"
                )

            elif hasattr(parsed, "data_value"):  # ReplyTelegram
                telegram_type = "reply"
                print(f"Auto-detected: {telegram_type.upper()}")
                if parsed.data_point_id == DataPointType.VERSION:
                    version_info = parsed.parsed_value
                    if version_info["parsed"]:
                        print(
                            f"  → Version reply: {version_info['formatted']} from device {parsed.serial_number}"
                        )
                    else:
                        print(
                            f"  → Version reply (unparseable) from device {parsed.serial_number}"
                        )
                else:
                    print(
                        f"  → {parsed.data_point_description} reply from device {parsed.serial_number}"
                    )

            elif hasattr(parsed, "system_function"):  # SystemTelegram
                telegram_type = "system"
                print(f"Auto-detected: {telegram_type.upper()}")
                if parsed.data_point_id == DataPointType.VERSION:
                    print(f"  → Version request from device {parsed.serial_number}")
                else:
                    print(
                        f"  → {parsed.data_point_description} request from device {parsed.serial_number}"
                    )
            else:
                telegram_type = "unknown"
                print(f"Auto-detected: {telegram_type.upper()}")
                print("  → Unknown telegram type")

            print(f"  Raw: {telegram_str}")
            print()

        except TelegramParsingError as e:
            print(f"Parse error: {telegram_str} - {e}")

    print("5. Version Service Integration:")
    print("-" * 31)

    # Demonstrate version service functionality
    raw_reply = "<R0020030837F02D02XP230_V1.00.04FI>"

    try:
        parsed_reply = telegram_service.parse_reply_telegram(raw_reply)
        version_result = version_service.parse_version_reply(parsed_reply)

        if version_result.success:
            summary = version_service.format_version_summary(version_result.data)
            print("Version Service Summary:")
            print("-" * 23)
            print(summary)
        else:
            print(f"Version parsing failed: {version_result.error}")

    except Exception as e:
        print(f"Error in version service demo: {e}")


def demo_version_edge_cases():
    """Demonstrate version parsing edge cases and error handling"""
    print("\n=== Version Parsing Edge Cases ===\n")

    telegram_service = TelegramService()
    version_service = VersionService()

    print("1. Invalid Version Formats:")
    print("-" * 27)

    # Test various invalid version formats
    invalid_versions = [
        "<R0020000000F02D02INVALID_FORMATXX>",  # No _V separator
        "<R0020000000F02D02XP24_V1.00XX>",  # Incomplete version
        "<R0020000000F02D02XP24_VX.YZ.ABXX>",  # Non-numeric version
        "<R0020000000F02D02_V1.00.04XX>",  # Missing product
    ]

    for telegram_str in invalid_versions:
        try:
            parsed = telegram_service.parse_reply_telegram(telegram_str)
            version_data = parsed.parsed_value

            print(f"Telegram: {telegram_str}")
            print(f"  Parsed: {version_data['parsed']}")
            if not version_data["parsed"] and "error" in version_data:
                print(f"  Error: {version_data['error']}")
            print(f"  Raw Value: {version_data['raw_value']}")
            print()

        except TelegramParsingError as e:
            print(f"Parse error: {telegram_str} - {e}")

    print("2. Edge Case Product Names:")
    print("-" * 26)

    # Test edge cases with unusual but valid product names
    edge_cases = [
        "<R0020000000F02D02A_V1.00.00XX>",  # Single char product
        "<R0020000000F02D02XP_33_LR_V1.00.00XX>",  # Multiple underscores
        "<R0020000000F02D02VERYLONGPRODUCT_V1.00.00XX>",  # Long product name
    ]

    for telegram_str in edge_cases:
        try:
            parsed = telegram_service.parse_reply_telegram(telegram_str)
            version_data = parsed.parsed_value

            print(f"Product: {version_data.get('product', 'PARSE_FAILED')}")
            print(f"Version: {version_data.get('version', 'PARSE_FAILED')}")
            print(f"Formatted: {version_data.get('formatted', 'PARSE_FAILED')}")
            print(f"Parsed: {version_data['parsed']}")
            print()

        except Exception as e:
            print(f"Error: {e}")

    print("3. Version Service Error Handling:")
    print("-" * 34)

    # Test version service error handling
    error_test_cases = [
        ("12345", "Invalid serial number length"),  # Too short
        ("123456789A", "Non-numeric serial number"),  # Non-numeric
        (None, "None input"),  # None input
    ]

    for serial, description in error_test_cases:
        result = version_service.generate_version_request_telegram(serial)
        print(f"{description}: {result.success}")
        if not result.success:
            print(f"  Error: {result.error}")
        print()


if __name__ == "__main__":
    print("XP System Demo - Telegram Events, Module Types & Version Parsing")
    print("=" * 70)

    demo_basic_parsing()
    demo_multiple_parsing()
    demo_validation()
    demo_input_types()
    demo_module_types()
    demo_enhanced_telegram_parsing()
    demo_version_parsing()
    demo_version_edge_cases()

    print("\n" + "=" * 70)
    print("Demo completed! Try running the CLI:")
    print("\n--- Event Telegram Commands ---")
    print("python -m xp.cli.main telegram parse '<E14L00I02MAK>'")
    print(
        "python -m xp.cli.main telegram parse-multiple 'Data <E14L00I02MAK> more <E14L01I03BB1>'"
    )
    print("python -m xp.cli.main telegram validate '<E14L00I02MAK>'")
    print("\n--- Version Commands ---")
    print("python -m xp.cli.main version request 0020030837")
    print("python -m xp.cli.main version parse '<R0020030837F02D02XP230_V1.00.04FI>'")
    print("python -m xp.cli.main telegram parse '<S0020030837F02D02FM>'")
    print("\n--- System & Reply Telegram Commands ---")
    print("python -m xp.cli.main telegram parse-system '<S0020030837F02D02FM>'")
    print("python -m xp.cli.main telegram parse-reply '<R0020030837F02D18+26.0§CIL>'")
    print("python -m xp.cli.main telegram parse '<R0020030837F02D02XP230_V1.00.04FI>'")
    print("\n--- Module Type Commands ---")
    print("python -m xp.cli.main module info 14")
    print("python -m xp.cli.main module list --group-by-category")
    print("python -m xp.cli.main module search 'push button'")
    print("python -m xp.cli.main module categories")
