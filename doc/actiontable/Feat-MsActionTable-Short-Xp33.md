# Feature: MsActionTable Short Format - XP33

## Overview

This document specifies a compact, human-readable short format for representing XP33 MsActionTable configurations. The short format provides a concise way to display and edit action table configurations for XP33 dimmer modules in CLI output and YAML files.

XP33 modules feature 3 dimming outputs with scene control, making the configuration significantly different from XP24's input-based action table.

## Goals

- Provide a human-readable compact representation of XP33 action table configurations
- Support all output configuration parameters and scene settings
- Enable easy comparison of dimmer and scene configurations
- Maintain consistency with existing XP24 short format pattern
- Support serialization and deserialization

## Format Specification

### XP33 Short Format

```
OUTX <output_cfg> 
SCENEX <scene_cfg>
```

**Components:**

1. **Module Type**: `XP33`
2. **Output Configuration**: Three output specifications with format `<min>-<max>[flags]`
3. **Scene Configuration**: Four scene specifications with format `<o1>/<o2>/<o3>@<time>`

**Example:**
```
OUT1 MIN:0 MAX:100 SO:0 SF:0 LE:0
OUT2 MIN:0 MAX:100 SO:0 SF:0 LE:0
OUT3 MIN:0 MAX:100 SO:0 SF:0 LE:0
SCENE1 OUT1:0 OUT2:0 OUT3:0 T:NONE
SCENE2 OUT1:0 OUT2:0 OUT3:0 T:NONE
SCENE3 OUT1:0 OUT2:0 OUT3:0 T:NONE
```

### Output Configuration Format

Each output is represented as: 
`OUT<num> MIN:<min> MAX:<max> SO:<scene_output> SF:<start_at_full> LE:<leading_edge>`

Where:
- `OUT<num>`: Output (0-2)
- `MIN:<min>`: Minimum output level (0-100)
- `MAX:<max>`: Maximum output level (0-100)
- `SO:<scene_output>`: Scene outputs enabled
- `SF<start_at_full>`: Start at full brightness
- `LE<leading_edge>`: Leading edge dimming

**Examples:**
```
OUT1 MIN:0 MAX:100 SO:0 SF:0 LE:0
```

### Scene Configuration Format

Each scene is represented as: 
`SCENE<num> OUT1:<o1> OUT2:<o2> OUT3:<o3> T:NONE`

Where:
- `SCENE<num>`: Scene (0-2)
- `OUT1:<o1>`: Output 1 level (0-100)
- `OUT2:<o2>`: Output 2 level (0-100)
- `OUT3:<o3>`: Output 3 level (0-100)
- `T:<time>`: TimeParam value (see TimeParam Values section below)

**Examples:**
```
SCENE1 OUT1:0 OUT2:0 OUT3:0 T:NONE
```

### TimeParam Values

TimeParam values can be specified using either the enum name or numeric value:

| Value  | Name    | Description       |
|--------|---------|-------------------|
| 0      | NONE    | No time parameter |
| 1      | T05SEC  | 0.5 second delay  |
| 2      | T1SEC   | 1 second delay    |
| 3      | T2SEC   | 2 second delay    |
| 4      | T5SEC   | 5 second delay    |
| 5      | T10SEC  | 10 second delay   |
| 6      | T15SEC  | 15 second delay   |
| 7      | T20SEC  | 20 second delay   |
| 8      | T30SEC  | 30 second delay   |
| 9      | T45SEC  | 45 second delay   |
| 10     | T1MIN   | 1 minute delay    |
| 11     | T2MIN   | 2 minute delay    |
| 12     | T5MIN   | 5 minute delay    |
| 13     | T10MIN  | 10 minute delay   |
| 14     | T15MIN  | 15 minute delay   |
| 15     | T20MIN  | 20 minute delay   |
| 16     | T30MIN  | 30 minute delay   |
| 17     | T45MIN  | 45 minute delay   |
| 18     | T60MIN  | 60 minute delay   |
| 19     | T120MIN | 120 minute delay  |

## Examples

### Basic Configuration (Default Settings)
```yaml
xp33_msaction_table:
  output1:
    min_level: 0
    max_level: 100
    scene_outputs: false
    start_at_full: false
    leading_edge: false
  output2:
    min_level: 0
    max_level: 100
    scene_outputs: false
    start_at_full: false
    leading_edge: false
  output3:
    min_level: 0
    max_level: 100
    scene_outputs: false
    start_at_full: false
    leading_edge: false
  scene1:
    output1_level: 0
    output2_level: 0
    output3_level: 0
    time: NONE
  scene2:
    output1_level: 0
    output2_level: 0
    output3_level: 0
    time: NONE
  scene3:
    output1_level: 0
    output2_level: 0
    output3_level: 0
    time: NONE
  scene4:
    output1_level: 0
    output2_level: 0
    output3_level: 0
    time: NONE
```

**Short format:**
```
OUT1 MIN:0 MAX:100 SO:0 SF:0 LE:0
OUT2 MIN:0 MAX:100 SO:0 SF:0 LE:0
OUT3 MIN:0 MAX:100 SO:0 SF:0 LE:0
SCENE1 OUT1:0 OUT2:0 OUT3:0 T:0
SCENE2 OUT1:0 OUT2:0 OUT3:0 T:0
SCENE3 OUT1:0 OUT2:0 OUT3:0 T:0
SCENE4 OUT1:0 OUT2:0 OUT3:0 T:0
```

### Dimmer Configuration with Limited Range
```yaml
xp33_msaction_table:
  output1:
    min_level: 10
    max_level: 90
    scene_outputs: true
    start_at_full: false
    leading_edge: true
  output2:
    min_level: 20
    max_level: 80
    scene_outputs: false
    start_at_full: true
    leading_edge: false
  output3:
    min_level: 30
    max_level: 70
    scene_outputs: true
    start_at_full: true
    leading_edge: true
  scene1:
    output1_level: 50
    output2_level: 60
    output3_level: 70
    time: T5SEC
  scene2:
    output1_level: 25
    output2_level: 35
    output3_level: 45
    time: T10SEC
  scene3:
    output1_level: 75
    output2_level: 85
    output3_level: 95
    time: T1MIN
  scene4:
    output1_level: 0
    output2_level: 100
    output3_level: 50
    time: NONE
```

**Short format:**
```
OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1
OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0
OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1
SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC
SCENE2 OUT1:25 OUT235 OUT3:45 T:T10SEC
SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN
SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE
```
### Scene Presets for Theater Lighting
```yaml
xp33_msaction_table:
  output1:
    min_level: 0
    max_level: 100
    scene_outputs: true
    start_at_full: false
    leading_edge: false
  output2:
    min_level: 0
    max_level: 100
    scene_outputs: true
    start_at_full: false
    leading_edge: false
  output3:
    min_level: 0
    max_level: 100
    scene_outputs: true
    start_at_full: false
    leading_edge: false
  scene1:
    output1_level: 100
    output2_level: 100
    output3_level: 100
    time: T2SEC
  scene2:
    output1_level: 50
    output2_level: 30
    output3_level: 20
    time: T5SEC
  scene3:
    output1_level: 0
    output2_level: 0
    output3_level: 100
    time: T10SEC
  scene4:
    output1_level: 0
    output2_level: 0
    output3_level: 0
    time: T1SEC
```

**Short format:**
```
OUT1 MIN:0 MAX:100 SO:1 SF:0 LE:0
OUT2 MIN:0 MAX:100 SO:1 SF:0 LE:0
OUT3 MIN:0 MAX:100 SO:1 SF:0 LE:0
SCENE1 OUT1:100 OUT2:100 OUT3:100 T:T2SEC
SCENE2 OUT1:50 OUT2:30 OUT3:20 T:T5SEC
SCENE3 OUT1:0 OUT2:0 OUT3:100 T:T10SEC
SCENE4 OUT1:0 OUT2:0 OUT3:0 T:T1SEC
```

## Implementation

### Model Methods

Add the following methods to `Xp33MsActionTable`:

```python
class Xp33MsActionTable(MsActionTable):

    def to_short_format(self) -> str:
        """Convert action table to short format string.

        Returns:
            Short format string (e.g., "XP33 O:0-100 0-100 0-100 S:0/0/0@NONE ...").
        """
        pass

    @classmethod
    def from_short_format(cls, short_str: str) -> "Xp33MsActionTable":
        """Parse short format string into action table.

        Args:
            short_str: Short format string.

        Returns:
            Xp33MsActionTable instance.

        Raises:
            ValueError: If format is invalid.
        """
        pass
```

### Helper Methods

Internal helper methods for encoding/decoding:

```python
@staticmethod
def _format_output(output: Xp33Output) -> str:
    """Format output configuration to short string.

    Args:
        output: Xp33Output instance.

    Returns:
        Short string like "10-90[SO+LE]".
    """
    pass

@staticmethod
def _parse_output(output_str: str) -> Xp33Output:
    """Parse output configuration from short string.

    Args:
        output_str: Short string like "10-90[SO+LE]".

    Returns:
        Xp33Output instance.

    Raises:
        ValueError: If format is invalid.
    """
    pass

@staticmethod
def _format_scene(scene: Xp33Scene) -> str:
    """Format scene configuration to short string.

    Args:
        scene: Xp33Scene instance.

    Returns:
        Short string like "50/60/70@T5SEC".
    """
    pass

@staticmethod
def _parse_scene(scene_str: str) -> Xp33Scene:
    """Parse scene configuration from short string.

    Args:
        scene_str: Short string like "50/60/70@T5SEC".

    Returns:
        Xp33Scene instance.

    Raises:
        ValueError: If format is invalid.
    """
    pass
```

### CLI Integration

The short format should be displayed in CLI output for:

1. **Download Command:**
```bash
$ xp conbus msactiontable download 0020045056 xp33
Module: A4 (0020045056)
Short: 
  - OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1
  - OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0
  - OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1
  - SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC
  - SCENE2 OUT1:25 OUT235 OUT3:45 T:T10SEC
  - SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN
  - SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE

```

2. **Show Command:**
```bash
$ xp conbus msactiontable show 0020045056
Module: A4 (0020045056)
Short: 
  - OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1
  - OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0
  - OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1
  - SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC
  - SCENE2 OUT1:25 OUT235 OUT3:45 T:T10SEC
  - SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN
  - SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE
Full:
  output1:
    min_level: 10
    max_level: 90
    scene_outputs: true
    start_at_full: false
    leading_edge: true
  ...
```

3. **List Command:**
```bash
$ xp conbus msactiontable list
Module: A4 (0020044991)
Module: A5 (0020045056)
```

## Testing Requirements

1. **Round-trip conversion**: `model.to_short_format()` → `from_short_format()` → should equal original
2. **All output configurations**: Test various min/max ranges and flag combinations
3. **All scene configurations**: Test various output levels and TimeParam values
4. **Flag combinations**: Test all combinations of SO, SA, LE flags
5. **Error handling**: Invalid format strings should raise ValueError
6. **Edge cases**:
   - Empty flags (no brackets)
   - Boundary values (0-100 for percentages, 0-19 for TimeParam)
   - Malformed strings (missing delimiters, invalid characters)
   - Invalid TimeParam values
   - Out of range percentages

## Differences from XP24

| Aspect         | XP24                                | XP33                                        |
|----------------|-------------------------------------|---------------------------------------------|
| Focus          | Input actions                       | Output control and scenes                   |
| Configuration  | 4 input actions + settings          | 3 outputs + 4 scenes                        |
| Action Types   | 28 different InputActionType values | N/A                                         |
| Output Control | N/A                                 | Min/max levels, dimming flags               |
| Scene Support  | Via SCENESET action type            | Direct scene configurations                 |
| Settings       | Mutex, curtain, deadtime            | Scene outputs, start behavior, dimming mode |

## References

- Related: `doc/actiontable/Feat-MsActionTable-Short-Xp24.md`
- Related: `doc/actiontable/Feature-Action-Table.md`
- Models: `src/xp/models/actiontable/msactiontable_xp33.py`
- Serializer: `src/xp/services/actiontable/msactiontable_xp33_serializer.py`