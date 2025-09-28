# Feature Specification: Download XP20 MsActionTable

## Overview
This specification defines the implementation of `Xp20MsActionTableSerializer` for encoding and decoding XP20 Action Table telegrams, based on the existing `Xp24MsActionTableSerializer` implementation.

## Data Structure

### XP20 Action Table Model
The `Xp20MsActionTable` contains:
- **8 Input Channels** (`input1` through `input8`): Each with configuration flags and function settings

### Input Channel Configuration (`InputChannel`)
- `invert`: bool - Input inversion flag
- `short_long`: bool - Short/long press detection flag
- `group_on_off`: bool - Group on/off function flag
- `and_functions`: list[bool] - AND function configuration array
- `sa_function`: bool - SA function flag
- `ta_function`: bool - TA function flag

## Telegram Format

### Example Telegram
```
AAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
```
This example represents a complete XP20 MsActionTable telegram.

### Data Layout (32 bytes total)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0      | 1    | Short/Long | Bit flags for short/long press (8 inputs) |
| 1      | 1    | Group On/Off | Bit flags for group on/off function (8 inputs) |
| 2      | 1    | Input Invert | Bit flags for input inversion (8 inputs) |
| 3-10   | 8    | AND Functions | AND function configuration data (8 inputs × 1 byte each) |
| 11     | 1    | SA Functions | Bit flags for SA function (8 inputs) |
| 12     | 1    | TA Functions | Bit flags for TA function (8 inputs) |
| 13-31  | 19   | Reserved | Padding/unused bytes |

### Input Channel Data Layout
Each input channel's configuration is distributed across the data layout:
- Input N short_long flag: Bit N in byte at offset `0`
- Input N group_on_off flag: Bit N in byte at offset `1`
- Input N invert flag: Bit N in byte at offset `2`
- Input N and_functions: Full byte at offset `3 + N` (where N is 0-7)
- Input N sa_function flag: Bit N in byte at offset `11`
- Input N ta_function flag: Bit N in byte at offset `12`

### Xp20MsActionTable Input Channel Mapping
Specific mapping for the 8 input channels in `Xp20MsActionTable`:

| Input Channel | Bit Position | short_long | group_on_off | invert | and_functions | sa_function | ta_function |
|---------------|--------------|------------|--------------|--------|---------------|-------------|-------------|
| input1        | 0            | short_long_index bit 0 | group_on_off_index bit 0 | invert_index bit 0 | and_functions_index[0] | sa_function_index bit 0 | ta_function_index bit 0 |
| input2        | 1            | short_long_index bit 1 | group_on_off_index bit 1 | invert_index bit 1 | and_functions_index[1] | sa_function_index bit 1 | ta_function_index bit 1 |
| input3        | 2            | short_long_index bit 2 | group_on_off_index bit 2 | invert_index bit 2 | and_functions_index[2] | sa_function_index bit 2 | ta_function_index bit 2 |
| input4        | 3            | short_long_index bit 3 | group_on_off_index bit 3 | invert_index bit 3 | and_functions_index[3] | sa_function_index bit 3 | ta_function_index bit 3 |
| input5        | 4            | short_long_index bit 4 | group_on_off_index bit 4 | invert_index bit 4 | and_functions_index[4] | sa_function_index bit 4 | ta_function_index bit 4 |
| input6        | 5            | short_long_index bit 5 | group_on_off_index bit 5 | invert_index bit 5 | and_functions_index[5] | sa_function_index bit 5 | ta_function_index bit 5 |
| input7        | 6            | short_long_index bit 6 | group_on_off_index bit 6 | invert_index bit 6 | and_functions_index[6] | sa_function_index bit 6 | ta_function_index bit 6 |
| input8        | 7            | short_long_index bit 7 | group_on_off_index bit 7 | invert_index bit 7 | and_functions_index[7] | sa_function_index bit 7 | ta_function_index bit 7 |

### Index Constants
Define these constants for clarity in implementation:
```python
short_long_index = 0
group_on_off_index = 1
invert_index = 2
and_functions_index = 3  # starts at 3, uses indices 3-10
sa_function_index = 11
ta_function_index = 12
```

### Bit Flag Encoding
For each configuration type, use `byteToBits()` conversion to extract boolean arrays:
- `shortLongFlags = byteToBits(raw[short_long_index])` - Short/long press flags (index 0)
- `groupOnOffFlags = byteToBits(raw[group_on_off_index])` - Group on/off function flags (index 1)
- `invertFlags = byteToBits(raw[invert_index])` - Input inversion flags (index 2)
- `andFunctions = raw[and_functions_index:and_functions_index+8]` - AND function data (indices 3-10)
- `saFunctionFlags = byteToBits(raw[sa_function_index])` - SA function flags (index 11)
- `taFunctionFlags = byteToBits(raw[ta_function_index])` - TA function flags (index 12)

Each bit array represents flags for inputs:
- Bit 0: Input 1
- Bit 1: Input 2
- ...
- Bit 7: Input 8

## Implementation Requirements

### Class: `Xp20MsActionTableSerializer`

#### Methods Required

##### `to_data(action_table: Xp20MsActionTable) -> str`
- Serialize `Xp20MsActionTable` to telegram hex string format
- Apply A-P nibble encoding
- Return hex string (64 characters for 32 bytes)

##### `from_data(msactiontable_rawdata: str) -> Xp20MsActionTable`
- Deserialize telegram data to `Xp20MsActionTable`
- Validate input length (64 characters for 32 bytes)
- Apply de-nibble decoding
- Parse data according to offset table above

#### Helper Methods

##### `_decode_input_channel(raw_bytes: bytearray, input_index: int) -> InputChannel`
- Extract input channel configuration from raw bytes
- Extract bit flags from appropriate offsets using `byteToBits()` conversion
- Map bit flags to input channel properties: `short_long`, `group_on_off`, `invert`, `sa_function`, `ta_function`, `and_functions`

##### `_byte_to_bits(byte_value: int) -> list[bool]`
- Python implementation of `byteToBits()` function
- Convert single byte to 8-bit boolean array
- Used for extracting bit flags from raw data

```python
def _byte_to_bits(byte_value: int) -> list[bool]:
    """Convert a byte value to 8-bit boolean array.
    """
    return [(byte_value & (1 << n)) != 0 for n in range(8)]
```

##### `_encode_input_channel(input_channel: InputChannel, input_index: int, raw_bytes: bytearray) -> None`
- Encode input channel configuration into raw bytes
- Set appropriate bit flags at correct offsets
- Handle boolean to bit conversion

## Parameter Mapping

### Boolean Values
- Direct mapping of boolean flags to bit positions
- Use bitwise operations for encoding/decoding

### AND Functions
- Handle `and_functions` list as bit array
- Map list indices to bit positions

## Error Handling
- Validate telegram length (64 characters for 32 bytes)
- Handle invalid boolean values gracefully
- Implement exception handling for bit extraction operations
- Default to `false` for all flags if extraction fails
- Provide meaningful error messages for malformed data

## Testing Requirements
- Unit tests for serialization/deserialization round-trip
- Test all input channel combinations
- Invalid input handling
- Boundary value testing

## Dependencies
- `Xp20MsActionTable`, `InputChannel` models
- `de_nibble` utility function
- Bit manipulation utilities

## quality
- run publish.sh --quality until the issues are all fixed