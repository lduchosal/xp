# Feature: MsActionTable Short Format

## Overview

This document specifies a compact, human-readable short format for representing MsActionTable configurations across XP20, XP24, and XP33 modules. The short format provides a concise way to display and edit action table configurations in CLI output and YAML files.

## Goals

- Provide a human-readable compact representation of action table configurations
- Support all InputActionType variants and TimeParam values
- Enable easy comparison of action table settings
- Maintain consistency with existing XP20 short format pattern
- Support serialization and deserialization

## Format Specification

### XP24 Short Format

```
XP24 <input1> <input2> <input3> <input4> | <settings>
```

**Components:**

1. **Module Type**: `XP24`
2. **Input Actions**: Four input action specifications in format `<type>:<param>`
3. **Settings** (required): Additional configuration flags

**Example:**
```
XP24 T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12
```

### Input Action Format

Each input action is represented as: `<ActionType>:<TimeParam>`

Where:
- `<ActionType>`: Short code for InputActionType (see mapping below)
- `<TimeParam>`: Integer value of TimeParam enum (0-19)

### InputActionType Short Codes

| Type | Code | Description |
|------|------|-------------|
| VOID | V | No action |
| ON | ON | Turn on action |
| OFF | OF | Turn off action |
| TOGGLE | T | Toggle action |
| BLOCK | BL | Block action |
| AUXRELAY | AX | Auxiliary relay action |
| MUTUALEX | MX | Mutual exclusion action |
| LEVELUP | LU | Level up action |
| LEVELDOWN | LD | Level down action |
| LEVELINC | LI | Level increment action |
| LEVELDEC | LC | Level decrement action |
| LEVELSET | LS | Level set action |
| FADETIME | FT | Fade time action |
| SCENESET | SS | Scene set action |
| SCENENEXT | SN | Scene next action |
| SCENEPREV | SP | Scene previous action |
| CTRLMETHOD | CM | Control method action |
| RETURNDATA | RD | Return data action |
| DELAYEDON | DO | Delayed on action |
| EVENTTIMER1 | E1 | Event timer 1 action |
| EVENTTIMER2 | E2 | Event timer 2 action |
| EVENTTIMER3 | E3 | Event timer 3 action |
| EVENTTIMER4 | E4 | Event timer 4 action |
| STEPCTRL | SC | Step control action |
| STEPCTRLUP | SU | Step control up action |
| STEPCTRLDOWN | SD | Step control down action |
| LEVELSETINTERN | LN | Level set internal action |
| FADE | FD | Fade action |
| LEARN | LR | Learn action |

### TimeParam Values

| Value | Name | Description |
|-------|------|-------------|
| 0 | NONE | No time parameter |
| 1 | T05SEC | 0.5 second delay |
| 2 | T1SEC | 1 second delay |
| 3 | T2SEC | 2 second delay |
| 4 | T5SEC | 5 second delay |
| 5 | T10SEC | 10 second delay |
| 6 | T15SEC | 15 second delay |
| 7 | T20SEC | 20 second delay |
| 8 | T30SEC | 30 second delay |
| 9 | T45SEC | 45 second delay |
| 10 | T1MIN | 1 minute delay |
| 11 | T2MIN | 2 minute delay |
| 12 | T5MIN | 5 minute delay |
| 13 | T10MIN | 10 minute delay |
| 14 | T15MIN | 15 minute delay |
| 15 | T20MIN | 20 minute delay |
| 16 | T30MIN | 30 minute delay |
| 17 | T45MIN | 45 minute delay |
| 18 | T60MIN | 60 minute delay |
| 19 | T120MIN | 120 minute delay |

### Settings Format (Required)

Settings must be appended after a pipe `|` separator:

```
| M12:<0|1> M34:<0|1> C12:<0|1> C34:<0|1> DT:<12|20>
```

Where:
- `M12`: mutex12 (0=false, 1=true)
- `M34`: mutex34 (0=false, 1=true)
- `C12`: curtain12 (0=false, 1=true)
- `C34`: curtain34 (0=false, 1=true)
- `DT`: mutual_deadtime (12=MS300, 20=MS500)

All settings fields are required in the short format.

## Examples

### Basic TOGGLE Configuration
```yaml
xp24_msaction_table:
  input1_action:
    type: TOGGLE
    param: 1
  input2_action:
    type: TOGGLE
    param: 2
  input3_action:
    type: TOGGLE
    param: 0
  input4_action:
    type: TOGGLE
    param: 0
  mutex12: false
  mutex34: false
  curtain12: false
  curtain34: false
  mutual_deadtime: 12
```

**Short format:**
```
XP24 T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12
```

### Mixed Action Types
```yaml
xp24_msaction_table:
  input1_action:
    type: ON
    param: 4
  input2_action:
    type: OFF
    param: 0
  input3_action:
    type: LEVELSET
    param: 12
  input4_action:
    type: SCENESET
    param: 11
  mutex12: false
  mutex34: false
  curtain12: false
  curtain34: false
  mutual_deadtime: 12
```

**Short format:**
```
XP24 ON:4 OF:0 LS:12 SS:11 | M12:0 M34:0 C12:0 C34:0 DT:12
```

### With Custom Settings
```yaml
xp24_msaction_table:
  input1_action:
    type: TOGGLE
    param: 0
  input2_action:
    type: TOGGLE
    param: 0
  input3_action:
    type: TOGGLE
    param: 0
  input4_action:
    type: TOGGLE
    param: 0
  mutex12: true
  mutex34: true
  curtain12: false
  curtain34: false
  mutual_deadtime: 20
```

**Short format:**
```
XP24 T:0 T:0 T:0 T:0 | M12:1 M34:1 C12:0 C34:0 DT:20
```

### All VOID (Disabled)
```yaml
xp24_msaction_table:
  input1_action:
    type: VOID
    param: 0
  input2_action:
    type: VOID
    param: 0
  input3_action:
    type: VOID
    param: 0
  input4_action:
    type: VOID
    param: 0
  mutex12: false
  mutex34: false
  curtain12: false
  curtain34: false
  mutual_deadtime: 12
```

**Short format:**
```
XP24 V:0 V:0 V:0 V:0 | M12:0 M34:0 C12:0 C34:0 DT:12
```

## Implementation

### Model Methods

Add the following methods to `Xp24MsActionTable`:

```python
class Xp24MsActionTable(BaseModel):

    def to_short_format(self) -> str:
        """Convert action table to short format string.

        Settings are always included (required).

        Returns:
            Short format string (e.g., "XP24 T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12").
        """
        pass

    @classmethod
    def from_short_format(cls, short_str: str) -> "Xp24MsActionTable":
        """Parse short format string into action table.

        Args:
            short_str: Short format string with required settings section.

        Returns:
            Xp24MsActionTable instance.

        Raises:
            ValueError: If format is invalid or settings are missing.
        """
        pass
```

### CLI Integration

The short format should be displayed in CLI output for:

1. **Download Command:**
```bash
$ xp conbus msactiontable download 0020044991 xp24
Module: A4 (0020044991)
Short: T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12
```

2. **Show Command:**
```bash
$ xp conbus msactiontable show 0020044991
Module: A4 (0020044991)
Short: T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12
Full:
  input1_action:
    type: TOGGLE
    param: T05SEC
  ...
```

3. **List Command:**
```bash
$ xp conbus msactiontable list
Module: A4 (0020044991) - T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12
Module: A5 (0020044992) - ON:4 OF:0 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12
```

## Testing Requirements

1. **Round-trip conversion**: `model.to_short_format()` → `from_short_format()` → should equal original
2. **All action types**: Test each InputActionType short code
3. **All time params**: Test each TimeParam value (0-19)
4. **Settings variations**: Test all settings combinations (mutex, curtain, deadtime)
5. **Error handling**: Invalid format strings should raise ValueError
6. **Missing settings**: Format without settings section should raise ValueError
7. **Edge cases**: Empty inputs, boundary values, malformed strings

## References

- Existing pattern: XP20 format `XP20 10 0 > 0 OFF`
- Related: `doc/actiontable/Feature-Action-Table.md`
- Models: `src/xp/models/actiontable/msactiontable_xp24.py`
