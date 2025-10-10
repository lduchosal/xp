# Feature Specification: Download XP33 MsActionTable

## Overview
This specification defines the implementation of `Xp33MsActionTableSerializer` for encoding and decoding XP33 Action Table telegrams, based on the existing `Xp24MsActionTableSerializer` implementation.

## Data Structure

### XP33 Action Table Model
The `Xp33MsActionTable` contains:
- **3 Outputs** (`output1`, `output2`, `output3`): Each with min/max levels and configuration flags
- **4 Scenes** (`scene1`, `scene2`, `scene3`, `scene4`): Each with output levels and timing

### Output Configuration (`Xp33Output`)
- `min_level`: int (0-100) - Minimum output level percentage
- `max_level`: int (0-100) - Maximum output level percentage
- `scene_outputs`: bool - Scene output enable flag
- `start_at_full`: bool - Start at full level flag
- `leading_edge`: bool - Dimming function flag

### Scene Configuration (`Xp33Scene`)
- `output1_level`: int (0-100) - Output 1 level percentage
- `output2_level`: int (0-100) - Output 2 level percentage
- `output3_level`: int (0-100) - Output 3 level percentage
- `time`: TimeParam - Scene timing parameter

## Telegram Format

### Example Telegram
```
AAAABOGEBOGEBOGEAABECIDMAADMFACIAABEBEBEAAGEGEGEAHAAAAAAAAAAAAAAAAAA
AAAAAAGEAAGEAAGEAABECIDMAADMFACIAABEBEBEAAGEGEGEAHAAAAAAAAAAAAAAAAAA
```
Theses 2 examples is are chars, representing 2 completes XP33 MsActionTable telegrams.

### Data Layout (32 bytes total)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0-1    | 2    | Output 1 Min/Max | `raw[0]` = min_level, `raw[1]` = max_level |
| 2-3    | 2    | Output 2 Min/Max | `raw[2]` = min_level, `raw[3]` = max_level |
| 4-5    | 2    | Output 3 Min/Max | `raw[4]` = min_level, `raw[5]` = max_level |
| 6-21   | 16   | Light Scenes | 4 scenes × 4 bytes each |
| 22     | 1    | Scene Outputs | Bit flags for scene_outputs |
| 23     | 1    | Start At Full | Bit flags for start_at_full |
| 24     | 1    | Dim Function | Bit flags for leading_edge |
| 25-31  | 7    | Padding | Reserved/unused |

### Scene Data Layout (Offset 6-21)
Each scene occupies 4 bytes:
- Scene N offset: `6 + (4 * scene_index)`
- Byte 0: Time parameter (`time.get(raw[offset])`)
- Byte 1: Output 1 level (`percentage.get(raw[offset + 1])`)
- Byte 2: Output 2 level (`percentage.get(raw[offset + 2])`)
- Byte 3: Output 3 level (`percentage.get(raw[offset + 3])`)

### Bit Flag Encoding
For bytes 22-24, use `byteToBits()` conversion to extract boolean arrays:
- `sceneOutputs = byteToBits(raw[22])` - Scene output enable flags
- `startAtFull = byteToBits(raw[23])` - Start at full level flags
- `dimFunction = byteToBits(raw[24])` - Dimming function flags (with exception handling)

Each bit array represents flags for outputs:
- Bit 0: Output 1
- Bit 1: Output 2
- Bit 2: Output 3
- Bits 3-7: Unused

## Implementation Requirements

### Class: `Xp33MsActionTableSerializer`

#### Methods Required

##### `to_data(action_table: Xp33MsActionTable) -> str`
- Serialize `Xp33MsActionTable` to telegram hex string format
- Apply A-P nibble encoding
- Return hex string (length may vary, example shows 136 characters total)

##### `from_data(msactiontable_rawdata: str) -> Xp33MsActionTable`
- Deserialize telegram data to `Xp33MsActionTable`
- Validate input length (example shows 136 characters total)
- Remove 4-character prefix (e.g., "AAAA")
- Apply de-nibble decoding
- Parse data according to offset table above

#### Helper Methods

##### `_decode_output(raw_bytes: bytearray, output_index: int) -> Xp33Output`
- Extract output configuration from raw bytes
- Read min/max levels from appropriate offsets: `raw[2 * output_index]`, `raw[2 * output_index + 1]`
- Extract bit flags from bytes 22-24 using `byteToBits()` conversion
- Map bit flags to output properties: `scene_outputs`, `start_at_full`, `leading_edge`

##### `_decode_scene(raw_bytes: bytearray, scene_index: int) -> Xp33Scene`
- Extract scene configuration from raw bytes
- Calculate scene offset: `6 + (4 * scene_index)`
- Parse time parameter and output levels

##### `_byte_to_bits(byte_value: int) -> List[bool]`
- Python implementation of `byteToBits()` function
- Convert single byte to 8-bit boolean array
- Used for extracting bit flags from raw data

```python
def _byte_to_bits(byte_value: int) -> List[bool]:
    """Convert a byte value to 8-bit boolean array.
    """
    return [(byte_value & (1 << n)) != 0 for n in range(8)]
```

## Parameter Mapping

### Percentage Values
- Use `percentage.get(value)` for level conversions
- Map 0-100 percentage to appropriate telegram values

### Time Parameters
- Use `time.get(value)` for timing conversions
- Map `TimeParam` enum to telegram values

## Error Handling
- Validate telegram length (example shows 136 characters total)
- Handle invalid percentage/time values gracefully
- Implement exception handling for `dimFunction` bit extraction (as shown in pseudo code)
- Default to `false` for all 3 outputs if `dimFunction` extraction fails
- Provide meaningful error messages for malformed data

## Testing Requirements
- Unit tests for serialization/deserialization round-trip
- Boundary value testing (min/max percentages)
- Invalid input handling

## Dependencies
- `Xp33MsActionTable`, `Xp33Output`, `Xp33Scene` models
- `TimeParam` enum
- `de_nibble` utility function
- Percentage and time parameter lookup tables