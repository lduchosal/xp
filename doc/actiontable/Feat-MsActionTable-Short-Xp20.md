# Feature: MsActionTable Short Format - XP20

## Overview

This document specifies a compact, human-readable short format for representing XP20 MsActionTable configurations. The short format provides a concise way to display and edit action table configurations in CLI output and YAML files.

## Goals

- Provide a human-readable compact representation of XP20 action table configurations
- Support all input channel flags (invert, short_long, group_on_off, sa_function, ta_function)
- Support 8-bit AND functions for each input channel
- Enable easy comparison of action table settings
- Support serialization and deserialization
- Maintain consistency with XP24/XP33 short format patterns

## Format Specification

### XP20 Short Format

```
CH1 I:0 S:0 G:0 AND:10000000 SA:0 TA:0
CH2 I:0 S:0 G:0 AND:01000000 SA:0 TA:0
CH3 I:0 S:0 G:0 AND:00100000 SA:0 TA:0
CH4 I:0 S:0 G:0 AND:00010000 SA:0 TA:0
CH5 I:0 S:0 G:0 AND:00001000 SA:0 TA:0
CH6 I:0 S:0 G:0 AND:00000100 SA:0 TA:0
CH7 I:0 S:0 G:0 AND:00000010 SA:0 TA:0
CH8 I:0 S:0 G:0 AND:00000001 SA:0 TA:0
```

**Components:**

1. **Module Type**: `XP20`
2. **Input Channels**: Eight input channel specifications, each encoding flags and AND functions

### Input Channel Format

Each input channel is represented with labeled fields:
```
CHX I:Y S:Y G:Y AND:YYYYYYYY SA:Y TA:Y
```

Where:
- `CHX`: Channel number (1-8)
- `I:Y`: Invert flag (0 or 1)
- `S:Y`: Short/long flag (0 or 1)
- `G:Y`: Group on/off flag (0 or 1)
- `AND:YYYYYYYY`: 8-digit binary value representing 8 AND function bits
- `SA:Y`: SA function flag (0 or 1)
- `TA:Y`: TA function flag (0 or 1)

### Flag Representation

Each flag is represented as a separate field with a 0 or 1 value:

| Field        | Description                        | Values |
|--------------|------------------------------------|--------|
| I            | Input inversion enabled            | 0 or 1 |
| S            | Short/long press detection enabled | 0 or 1 |
| G            | Group on/off function enabled      | 0 or 1 |
| AND          | 8-bit AND functions                | 8-digit binary |
| SA           | SA function enabled                | 0 or 1 |
| TA           | TA function enabled                | 0 or 1 |


### AND Functions Binary Encoding

The 8 AND function bits are encoded as an 8-digit binary string:

| Binary (bits 7-0) | Hex  | Description                     |
|-------------------|------|---------------------------------|
| 00000000          | 0x00 | All AND functions disabled      |
| 11111111          | 0xFF | All AND functions enabled       |
| 10101010          | 0xAA | Alternating pattern (even bits) |
| 01010101          | 0x55 | Alternating pattern (odd bits)  |

**Bit order:** LSB (bit 0) to MSB (bit 7) represents and_functions[0] to and_functions[7]


## Examples

### All Channels Disabled (Default)

```yaml
xp20_msaction_table:
  input1:
    invert: false
    short_long: false
    group_on_off: false
    and_functions: [false, false, false, false, false, false, false, false]
    sa_function: false
    ta_function: false
  input2:
    invert: false
    short_long: false
    group_on_off: false
    and_functions: [false, false, false, false, false, false, false, false]
    sa_function: false
    ta_function: false
  # ... input3-input8 same as input1
```

**Short format:**
```
CH1 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
CH2 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
...
```

### Mixed Configuration

```yaml
xp20_msaction_table:
  input1:
    invert: true
    short_long: false
    group_on_off: true
    and_functions: [true, false, true, false, true, false, true, false]  # 0x55
    sa_function: false
    ta_function: true
  input2:
    invert: false
    short_long: true
    group_on_off: false
    and_functions: [false, true, false, true, false, true, false, true]  # 0xAA
    sa_function: true
    ta_function: false
  input3:
    invert: true
    short_long: true
    group_on_off: true
    and_functions: [true, true, false, false, true, true, false, false]  # 0x33
    sa_function: true
    ta_function: true
  input4:
    invert: false
    short_long: false
    group_on_off: false
    and_functions: [false, false, false, false, false, false, false, false]
    sa_function: false
    ta_function: false
  # ... input5-input8 same as input4 (defaults)
```

**Short format:**
```
CH1 I:1 S:0 G:1 AND:10101010 SA:0 TA:1
CH2 I:0 S:1 G:0 AND:01010101 SA:1 TA:0
CH3 I:1 S:1 G:1 AND:11001100 SA:1 TA:1
CH4 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
```

## Implementation

### Model Methods

Add the following methods to `Xp20MsActionTable`:

```python
class Xp20MsActionTable(BaseModel):

    def to_short_format(self) -> str:
        """Convert action table to short format string.

        Returns:
            Short format string with each channel on a separate line.
            Example:
                CH1 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
                CH2 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
                ...
        """
        pass

    @classmethod
    def from_short_format(cls, short_str: str) -> "Xp20MsActionTable":
        """Parse short format string into action table.

        Args:
            short_str: Short format string.

        Returns:
            Xp20MsActionTable instance.

        Raises:
            ValueError: If format is invalid.
        """
        pass
```

### Serializer Integration

Update `Xp20MsActionTableSerializer.format_decoded_output()` to use the short format:

```python
@staticmethod
def format_decoded_output(action_table: Xp20MsActionTable) -> str:
    """Serialize XP20 action table to human-readable compact format.

    Args:
        action_table: XP20 action table to serialize

    Returns:
        Human-readable string describing XP20 action table
    """
    return action_table.to_short_format()
```

## CLI Integration

The short format should be displayed in CLI output for:

1. **Download Command:**
```bash
$ xp conbus msactiontable download 0020044991 xp20
Module: A4 (0020044991)
Short:
  - CH1 I:1 S:0 G:1 AND:10101010 SA:0 TA:1
  - CH2 I:0 S:1 G:0 AND:01010101 SA:1 TA:0
  - CH3 I:1 S:1 G:1 AND:11001100 SA:1 TA:1
  - CH4 I:0 S:0 G:0 AND:00000000 SA:0 TA:0

```

2. **Show Command:**
```bash
$ xp conbus msactiontable show 0020044991
Module: A4 (0020044991)
Short: 
  - CH1 I:1 S:0 G:1 AND:10101010 SA:0 TA:1
  - CH2 I:0 S:1 G:0 AND:01010101 SA:1 TA:0
  - CH3 I:1 S:1 G:1 AND:11001100 SA:1 TA:1
  - CH4 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
Full:
  input1:
    invert: true
    short_long: false
    group_on_off: false
    and_functions: [false, false, false, false, false, false, false, false]
    sa_function: false
    ta_function: false
  ...
```

3. **List Command:**
```bash
$ xp conbus msactiontable list
Module: A4 (0020044991) 
Module: A5 (0020044992) 
```

## Testing Requirements

1. **Round-trip conversion**: `model.to_short_format()` → `from_short_format()` → should equal original
2. **All flag combinations**: Test each flag individually and in combination
3. **AND functions**: Test all binary patterns (00000000, 11111111, 10101010, 01010101, etc.)
4. **Default channels**: Test channels with all defaults (all zeros)
5. **Error handling**: Invalid format strings should raise ValueError
6. **Edge cases**:
   - All flags disabled (all zeros)
   - All flags enabled (all ones)
   - Invalid binary values (non 0/1 characters in AND field)
   - Wrong number of channels (not 8)
   - Malformed strings (missing fields, wrong field names)
   - Invalid channel numbers (not 1-8)

## Format Validation

Each line must match the pattern:
```regex
^CH([1-8]) I:([01]) S:([01]) G:([01]) AND:([01]{8}) SA:([01]) TA:([01])$
```

Where:
- `CH([1-8])`: Channel number from 1 to 8
- `I:([01])`: Invert flag, 0 or 1
- `S:([01])`: Short/long flag, 0 or 1
- `G:([01])`: Group on/off flag, 0 or 1
- `AND:([01]{8})`: Exactly 8 binary digits (0 or 1)
- `SA:([01])`: SA function flag, 0 or 1
- `TA:([01])`: TA function flag, 0 or 1
- Single spaces separate each field
- Each channel must appear on a separate line

## References

- Related: `doc/actiontable/Feat-MsActionTable-Short-Xp24.md`
- Related: `doc/actiontable/Feature-Action-Table.md`
- Models: `src/xp/models/actiontable/msactiontable_xp20.py`
- Serializer: `src/xp/services/actiontable/msactiontable_xp20_serializer.py`