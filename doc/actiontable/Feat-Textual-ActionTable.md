# Textual Action Table Format

Add textual output format for action tables in addition to existing JSON format

## Format Comparison

### Textual Format (New)
```
CP20 0 0 > 1 OFF;
CP20 0 0 > 2 OFF;
CP20 0 1 > 1 ~ON;
CP20 0 1 > 2 ON;
```

**Format:**
```
<Type> <Link> <Input> > <Output> <Command> [<Parameter>];
```

### JSON Format (Existing)
```json
{
  "module_type": "ModuleTypeCode.CP20",
  "link_number": 0,
  "module_input": 0,
  "module_output": 1,
  "command": "InputActionType.TURNOFF",
  "parameter": 0,
  "inverted": false
}
```

## CLI

### Download with Format Option

add actiontable_short to the existing output

```bash
xp conbus actiontable download <serial_number>
```

### Output Examples

**Output:**
```json
{
  "serial_number": "0020044991",
  "actiontable_short": [
    "CP20 0 0 > 1 OFF;",
    "CP20 0 0 > 2 OFF;",
    "CP20 0 0 > 3 OFF;",
    "CP20 0 0 > 4 OFF;",
    "CP20 0 1 > 1 ~ON;",
    "CP20 0 1 > 2 ON;",
    "CP20 0 1 > 3 ON;",
    "CP20 0 1 > 4 ON;"
  ],
  "actiontable": [
    {
      "module_type": "ModuleTypeCode.CP20",
      "link_number": 0,
      "module_input": 0,
      "module_output": 1,
      "command": "InputActionType.TURNOFF",
      "parameter": 0,
      "inverted": false
    }
  ]
}
```

## Implementation Plan

### Existing Implementation

**File:** `src/xp/services/actiontable/actiontable_serializer.py` *(existing)*

A `format_decoded_output` method already exists (line 143-169) that implements the textual format:

**Current implementation:**
- Formats entries as: `CP20 0 0 > 1 OFF;`
- Uses `module_type.name` and `command.name` for simplified output
- Handles inverted flag with `~` prefix
- Includes semicolon `;` at end of each line

**Differences from proposed format:**
1. **Parameter**: Current doesn't display parameter values
2. **Line joining**: Current joins with newlines, proposed needs list of strings

### Service Layer

**File:** `src/xp/services/actiontable/actiontable_serializer.py` *(existing)*

**Modify:** `ActionTableSerializer.format_decoded_output()`

**Changes needed:**
1. Add parameter display when `entry.parameter` is not None and value != 0
2. Add new method `format_decoded_list()` that returns list of strings

**Updated format logic:**
```python
@staticmethod
def format_decoded_output(action_table: ActionTable) -> list[str]:
    """Format ActionTable as human-readable decoded output.

    Args:
        action_table: ActionTable to format

    Returns:
        Human-readable string representation
    """
    lines = []
    for entry in action_table.entries:
        # Format: CP20 0 0 > 1 OFF [param];
        module_type = entry.module_type.name
        link = entry.link_number
        input_num = entry.module_input
        output = entry.module_output
        command = entry.command.name

        # Add prefix for inverted commands
        if entry.inverted:
            command = f"~{command}"

        # Build base line
        line = f"{module_type} {link} {input_num} > {output} {command}"

        # Add parameter if present and non-zero
        if entry.parameter is not None and entry.parameter.value != 0:
            line += f" {entry.parameter.value}"

        # Add semicolon terminator
        line += ";"

        lines.append(line)

    return lines
```

### CLI Layer

**File:** `src/xp/cli/commands/conbus_actiontable_commands.py` *(existing)*

CLI usage is not affected. Output response includes new `actiontable_short` field.

**Implementation:**
- Call `ActionTableSerializer.format_decoded_list()` to generate textual entries
- Add `actiontable_short` field to response containing list of formatted strings
- Maintain existing `actiontable` field with JSON format for backward compatibility

**Example:**
```python
# In download command handler
action_table = await service.download_actiontable(serial_number)

# Generate textual format list
actiontable_short = ActionTableSerializer.format_decoded_list(action_table)

return {
    "serial_number": serial_number,
    "actiontable_short": actiontable_short,
    "actiontable": action_table.entries  # JSON format
}
```

### Testing Layer

#### Unit Tests

**File:** `tests/unit/test_services/test_actiontable_serializer.py` *(may need to create)*

**Test methods for modified `format_decoded_output()`:**
- `test_format_decoded_output_with_parameter()` - Verify parameter display when non-zero
- `test_format_decoded_output_parameter_zero()` - Verify parameter=0 is omitted
- `test_format_decoded_output_inverted()` - Verify ~prefix handling
- `test_format_decoded_output_empty()` - Empty action table
- `test_format_decoded_output_semicolon()` - Verify semicolon present

**Test methods for new `format_decoded_list()`:**
- `test_format_decoded_list_returns_list()` - Returns list type
- `test_format_decoded_list_entries_match()` - Each entry formatted correctly
- `test_format_decoded_list_empty()` - Empty table returns empty list

**File:** `tests/unit/test_cli/test_conbus_actiontable_commands.py` *(existing)*

**Test methods:**
- `test_download_actiontable_includes_short_format()` - Verify actiontable_short field exists
- `test_download_actiontable_short_format_correct()` - Verify format matches spec with semicolons
- `test_download_actiontable_backward_compatible()` - JSON field still present

#### Integration Tests

**File:** `tests/integration/test_actiontable_integration.py` *(existing)*

**Test methods:**
- `test_download_textual_format_integration()`
- `test_format_conversion_roundtrip()`

### Model Layer

**File:** `src/xp/models/actiontable.py` *(existing)*

**No changes required** - existing models support both formats

### Textual Format Specification

**Components:**
- `module_type`: Module type code (e.g., CP20, XP24)
- `link_number`: Link number (0-255)
- `module_input`: Input number (0-255)
- `>`: Separator
- `module_output`: Output number (0-255)
- `inverted`: Prefix `~` if true, nothing if false
- `command`: Command type (ON, OFF, TOGGLE, etc.)
- `parameter`: Optional parameter (time, value, etc.)

**Examples:**
```
CP20 0 0 > 1 OFF;          # Normal OFF command
CP20 0 1 > 1 ~ON;          # Inverted ON command
CP20 0 2 > 1 ON 500;       # ON with 500ms parameter
XP24 1 3 > 2 TOGGLE;       # TOGGLE on XP24 module
```

**Enum Serialization:**
- JSON format uses full enum representation: `"ModuleTypeCode.CP20"`, `"InputActionType.TURNOFF"`
- Textual format uses simplified names: `"CP20"`, `"OFF"`
- Conversion: Strip enum class prefix when formatting to textual, use enum `.name` attribute

### Error Handling and Validation

**Value Range Validation:**
- `link_number`: 0-255 (raise `ValueError` if out of range)
- `module_input`: 0-255 (raise `ValueError` if out of range)
- `module_output`: 0-255 (raise `ValueError` if out of range)
- `parameter`: 0-65535 or None (raise `ValueError` if invalid)

**Type Validation:**
- `module_type`: Must be valid `ModuleTypeCode` enum value
- `command`: Must be valid `InputActionType` enum value
- Unknown module types or commands should raise `ValueError`

**Edge Cases:**
- Empty action table: Return empty list `[]`
- Parameter value of 0: Omit from output (e.g., `"CP20 0 0 > 1 ON;"`)
- Parameter value non-zero: Include in output (e.g., `"CP20 0 2 > 1 ON 500;"`)
- Missing parameter (None): Omit from output (e.g., `"CP20 0 0 > 1 OFF;"`)

**Error Messages:**
- Clear, descriptive error messages indicating which field failed validation
- Include actual value and expected range in error messages

**Example validation:**
```python
def validate_entry(entry: ActionTableEntry) -> None:
    """Validate action table entry values."""
    if not 0 <= entry.link_number <= 255:
        raise ValueError(f"link_number {entry.link_number} out of range [0-255]")
    if not 0 <= entry.module_input <= 255:
        raise ValueError(f"module_input {entry.module_input} out of range [0-255]")
    if not 0 <= entry.module_output <= 255:
        raise ValueError(f"module_output {entry.module_output} out of range [0-255]")
    if entry.parameter is not None and not 0 <= entry.parameter <= 65535:
        raise ValueError(f"parameter {entry.parameter} out of range [0-65535]")
```

### Summary

Implementation enhances existing textual format in ActionTableSerializer:

1. **Modify existing method** - Add parameter support to `format_decoded_output()`
2. **Add list helper** - New `format_decoded_list()` method for CLI use
3. **CLI integration** - Add `actiontable_short` field to download response
4. **Test coverage** - Add test cases for parameter display and list format
5. **Backward compatible** - JSON format unchanged, semicolons preserved

Benefits:
- Human-readable output
- Compatible with conson.yml configuration
- Easy copy/paste for configuration
- Matches documentation examples

## Quality
- run sh publish.sh --quality until all issues are fixed