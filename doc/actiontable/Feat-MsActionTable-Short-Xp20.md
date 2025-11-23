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
CH:1 I:0 S:0 G:0 AND:10000000 A:0 TA:0
CH:2 I:0 S:0 G:0 AND:01000000 A:0 TA:0
CH:3 I:0 S:0 G:0 AND:00100000 A:0 TA:0
CH:4 I:0 S:0 G:0 AND:00010000 A:0 TA:0
CH:5 I:0 S:0 G:0 AND:00001000 A:0 TA:0
CH:6 I:0 S:0 G:0 AND:00000100 A:0 TA:0
CH:7 I:0 S:0 G:0 AND:00000010 A:0 TA:0
CH:8 I:0 S:0 G:0 AND:00000001 A:0 TA:0
```

**Components:**

1. **Module Type**: `XP20`
2. **Input Channels**: Eight input channel specifications, each encoding flags and AND functions

### Input Channel Format

Each input channel is represented as: `<flags>:<and_functions_hex>`

Where:
- `<flags>`: Compact flag representation (see below)
- `<and_functions_hex>`: 2-digit hexadecimal value (00-FF) representing 8 AND function bits

### Flag Representation

Flags are represented as a string of characters, where each present flag adds a character:

| Flag         | Character | Description                        |
|--------------|-----------|------------------------------------|
| invert       | I         | Input inversion enabled            |
| short_long   | S         | Short/long press detection enabled |
| group_on_off | G         | Group on/off function enabled      |
| and_function | AND       | AND Functions                      |
| sa_function  | A         | SA function enabled                |
| ta_function  | T         | TA function enabled                |


### AND Functions Hexadecimal Encoding

The 8 AND function bits are encoded as a 2-digit hexadecimal value:

| Bits (7-0)  |  Example                    |
|-------------|-----------------------------|
| 00000000    |  All AND functions disabled |
| 11111111    |  All AND functions enabled  |
| 10101010    |  Alternating pattern        |
| 01010101    |  Alternating pattern        |

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
CH:1 I:0 S:0 G:0 AND:00000000 A:0 TA:0
CH:2 I:0 S:0 G:0 AND:00000000 A:0 TA:0
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
CH:1 I:1 S:0 G:1 AND:10101010 A:0 TA:1
CH:2 I:0 S:1 G:0 AND:01010101 A:1 TA:0
CH:3 I:1 S:1 G:1 AND:11001100 A:1 TA:1
CH:4 I:0 S:0 G:0 AND:00000000 A:0 TA:0
```

## Implementation

### Model Methods

Add the following methods to `Xp20MsActionTable`:

```python
class Xp20MsActionTable(BaseModel):

    def to_short_format(self) -> str:
        """Convert action table to short format string.

        Returns:
            Short format string (e.g., "XP20 -:00 -:00 -:00 -:00 -:00 -:00 -:00 -:00").
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
Short: XP20 -:00 -:00 -:00 -:00 -:00 -:00 -:00 -:00
```

2. **Show Command:**
```bash
$ xp conbus msactiontable show 0020044991
Module: A4 (0020044991)
Short: XP20 I:00 I:00 -:00 -:00 -:00 -:00 -:00 -:00
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
Module: A4 (0020044991) - XP20 -:00 -:00 -:00 -:00 -:00 -:00 -:00 -:00
Module: A5 (0020044992) - XP20 I:FF -:AA -:00 -:00 -:00 -:00 -:00 -:00
```

## Testing Requirements

1. **Round-trip conversion**: `model.to_short_format()` → `from_short_format()` → should equal original
2. **All flag combinations**: Test each flag individually and in combination
3. **AND functions**: Test all hex values (0x00, 0xFF, 0x55, 0xAA, etc.)
4. **Default channels**: Test channels with all defaults
5. **Error handling**: Invalid format strings should raise ValueError
6. **Edge cases**:
   - Empty flags (dash representation)
   - All flags enabled
   - Invalid hex values
   - Wrong number of channels
   - Malformed strings

## Format Validation

Valid format must match:
```
^XP20(?: [A-Z\-]+:[0-9A-F]{2}){8}$
```

Where:
- Exactly 8 channel specifications
- Each channel has flags (letters A-Z or dash) followed by colon and 2-digit hex
- Spaces separate module type and channels

## References

- Related: `doc/actiontable/Feat-MsActionTable-Short-Xp24.md`
- Related: `doc/actiontable/Feature-Action-Table.md`
- Models: `src/xp/models/actiontable/msactiontable_xp20.py`
- Serializer: `src/xp/services/actiontable/msactiontable_xp20_serializer.py`