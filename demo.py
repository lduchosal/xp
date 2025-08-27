#!/usr/bin/env python3
"""
Demo script showing the Telegram Event parsing functionality.
This demonstrates the implemented feature from Feature-Telegram-Event.md
"""

import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from xp.services.telegram_service import TelegramService, TelegramParsingError
from xp.services.module_type_service import ModuleTypeService, ModuleTypeNotFoundError
from xp.models.event_telegram import EventType, InputType
from xp.models.module_type import ModuleType


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


def demo_multiple_parsing():
    """Demonstrate parsing multiple telegrams from data stream"""
    print("\n=== Multiple Telegram Parsing Demo ===\n")
    
    service = TelegramService()
    data_stream = (
        "System startup... <E14L00I02MAK> button pressed, "
        "processing... <E14L00I02BB1> button released, "
        "IR remote signal <E14L00I25MIR> detected, "
        "proximity sensor <E14L00I90MPS> activated."
    )
    
    print("Data stream:")
    print(data_stream)
    print("\nParsed telegrams:")
    
    telegrams = service.parse_multiple_telegrams(data_stream)
    for i, telegram in enumerate(telegrams, 1):
        print(f"{i}. {telegram}")


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
        except TelegramParsingError as e:
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
            print(f"{telegram.input_number:<8} | {telegram.input_type.value:<16} | {description:<20} | {telegram_str}")
        except TelegramParsingError as e:
            print(f"{'ERROR':<8} | {'N/A':<16} | {description:<20} | {telegram_str}")


def demo_module_types():
    """Demonstrate module type functionality"""
    print("\n=== Module Type Functionality Demo ===\n")
    
    service = ModuleTypeService()
    
    print("1. Module Type Lookup:")
    print("-" * 25)
    
    # Demonstrate lookup by code and name
    test_cases = [
        (14, "XP2606"),
        (7, "XP24"), 
        (3, "CP70A"),
        (22, "XPX1_8")
    ]
    
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
            print(f"  Example: {modules[0].name}")
    print()


def demo_enhanced_telegram_parsing():
    """Demonstrate enhanced telegram parsing with module information"""
    print("\n=== Enhanced Telegram Parsing Demo ===\n")
    
    telegram_service = TelegramService()
    
    # Test telegrams with different module types
    test_telegrams = [
        "<E14L00I02MAK>",  # XP2606 - Push button panel
        "<E7L01I01MR1>",   # XP24 - Relay module  
        "<E3L00I15MIR>",   # CP70A - IR link module
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
                print(f"Module: {telegram.module_info.name} - {telegram.module_info.description}")
                print(f"Category: {telegram.module_info.category}")
            else:
                print("Module: Unknown module type")
                
            print(f"Input Type: {telegram.input_type.value}")
            print("-" * 65)
            
        except TelegramParsingError as e:
            print(f"Error parsing {telegram_str}: {e}")
            print("-" * 65)


if __name__ == "__main__":
    print("XP System Demo - Telegram Events & Module Types")
    print("=" * 60)
    
    demo_basic_parsing()
    demo_multiple_parsing()
    demo_validation()
    demo_input_types()
    demo_module_types()
    demo_enhanced_telegram_parsing()
    
    print("\n" + "=" * 60)
    print("Demo completed! Try running the CLI:")
    print("\n--- Telegram Commands ---")
    print("python -m xp.cli.main telegram parse '<E14L00I02MAK>'")
    print("python -m xp.cli.main telegram parse-multiple 'Data <E14L00I02MAK> more <E14L01I03BB1>'")
    print("python -m xp.cli.main telegram validate '<E14L00I02MAK>'")
    print("\n--- Module Type Commands ---")
    print("python -m xp.cli.main module info 14")
    print("python -m xp.cli.main module list --group-by-category")
    print("python -m xp.cli.main module search 'push button'")
    print("python -m xp.cli.main module categories")