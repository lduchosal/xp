# Feature: Click Type Serial Number

## Overview
Custom Click parameter type for validating and formatting serial numbers.

## Requirements
- Accept string input
- Must be exactly 10 characters after processing
- Contains only numeric characters (0-9)
- If input length < 10: pad left with zeros
- If input length > 10: raise validation error
- Return formatted serial string

## Implementation
The `SerialNumberParamType` class extends Click's `ParamType` to provide:
- Input validation for numeric-only strings
- Automatic left-padding with zeros for short inputs
- Error handling for oversized inputs
- Consistent 10-character serial output

## Usage
```python
@click.command()
@click.option('serial_number', type=SERIAL_NUMBER)
def command(serial_number):
    # serial is guaranteed to be 10-digit string
    pass
```

## Examples
- Input: `"123"` → Output: `"0000000123"`
- Input: `"1234567890"` → Output: `"1234567890"`
- Input: `"12345678901"` → Error: Invalid serial length
- Input: `"123abc"` → Error: Non-numeric characters

## Implementation
./src/cli/utils/serial_number_type.py
./test/unit/test_cli/test_serial_number_type.py

## Test
Fully tested in test unit 

## Code base modification
./cli/commands/*.py 
add type=SERIAL_NUMBER where option is 'serial_number'