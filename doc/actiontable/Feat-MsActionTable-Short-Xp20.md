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
XP20 <ch1> <ch2> <ch3> <ch4> <ch5> <ch6> <ch7> <ch8>
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

| Flag | Character | Description |
|------|-----------|-------------|
| invert | I | Input inversion enabled |
| short_long | S | Short/long press detection enabled |
| group_on_off | G | Group on/off function enabled |
| sa_function | A | SA function enabled |
| ta_function | T | TA function enabled |

- If no flags are set: use `-` (dash) to represent empty flags
- Flags should appear in alphabetical order when multiple are set: A, G, I, S, T
- Examples:
  - No flags: `-:00`
  - Only invert: `I:00`
  - Invert + SA: `AI:00`
  - All flags: `AGIST:FF`

### AND Functions Hexadecimal Encoding

The 8 AND function bits are encoded as a 2-digit hexadecimal value:

| Bits (7-0) | Hex Value | Example |
|------------|-----------|---------|
| 00000000 | 00 | All AND functions disabled |
| 11111111 | FF | All AND functions enabled |
| 10101010 | AA | Alternating pattern |
| 01010101 | 55 | Alternating pattern |

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
XP20 -:00 -:00 -:00 -:00 -:00 -:00 -:00 -:00
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
XP20 GIT:55 AS:AA AGIST:33 -:00 -:00 -:00 -:00 -:00
```

**Explanation:**
- `GIT:55` - input1: Group, Invert, TA function enabled, AND functions = 0x55
- `AS:AA` - input2: SA, Short/long enabled, AND functions = 0xAA
- `AGIST:33` - input3: All flags enabled, AND functions = 0x33
- `-:00` - input4-8: No flags, no AND functions

### Only Invert Flags Set

```yaml
xp20_msaction_table:
  input1:
    invert: true
    short_long: false
    group_on_off: false
    and_functions: [false, false, false, false, false, false, false, false]
    sa_function: false
    ta_function: false
  input2:
    invert: true
    short_long: false
    group_on_off: false
    and_functions: [false, false, false, false, false, false, false, false]
    sa_function: false
    ta_function: false
  # ... input3-input8 defaults
```

**Short format:**
```
XP20 I:00 I:00 -:00 -:00 -:00 -:00 -:00 -:00
```

### AND Functions Only

```yaml
xp20_msaction_table:
  input1:
    invert: false
    short_long: false
    group_on_off: false
    and_functions: [true, true, true, true, true, true, true, true]  # 0xFF
    sa_function: false
    ta_function: false
  # ... input2-input8 defaults
```

**Short format:**
```
XP20 -:FF -:00 -:00 -:00 -:00 -:00 -:00 -:00
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

### Helper Functions

```python
def _channel_to_short(channel: InputChannel) -> str:
    """Convert InputChannel to short format representation.

    Args:
        channel: InputChannel to convert

    Returns:
        Short format string (e.g., "GIT:55", "-:00")
    """
    # Build flags string
    flags = []
    if channel.sa_function:
        flags.append('A')
    if channel.group_on_off:
        flags.append('G')
    if channel.invert:
        flags.append('I')
    if channel.short_long:
        flags.append('S')
    if channel.ta_function:
        flags.append('T')

    flags_str = ''.join(flags) if flags else '-'

    # Convert AND functions list to hex byte
    and_byte = 0
    for i, bit in enumerate(channel.and_functions[:8]):
        if bit:
            and_byte |= (1 << i)

    return f"{flags_str}:{and_byte:02X}"


def _short_to_channel(short: str) -> InputChannel:
    """Parse short format string into InputChannel.

    Args:
        short: Short format string (e.g., "GIT:55", "-:00")

    Returns:
        InputChannel instance

    Raises:
        ValueError: If format is invalid
    """
    # Split on colon
    parts = short.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid channel format: {short}")

    flags_str, and_hex = parts

    # Parse flags
    invert = 'I' in flags_str
    short_long = 'S' in flags_str
    group_on_off = 'G' in flags_str
    sa_function = 'A' in flags_str
    ta_function = 'T' in flags_str

    # Parse AND functions hex
    try:
        and_byte = int(and_hex, 16)
    except ValueError:
        raise ValueError(f"Invalid hex value in channel: {and_hex}")

    # Convert byte to bool list
    and_functions = [(and_byte >> i) & 1 == 1 for i in range(8)]

    return InputChannel(
        invert=invert,
        short_long=short_long,
        group_on_off=group_on_off,
        and_functions=and_functions,
        sa_function=sa_function,
        ta_function=ta_function
    )
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