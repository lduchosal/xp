# Textual Action Table Format

Add textual output format for action tables in addition to existing JSON format

## Format Comparison

### Textual Format (New)
```
CP20 0 0 > 1 OFF
CP20 0 0 > 2 OFF
CP20 0 1 > 1 ~ON
CP20 0 1 > 2 ON
```

**Format:**
```
<Type> <Link> <Input> > <Output> <Command> <Parameter>;
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

** output:**
```json
{
  "serial_number": "0020044991",
  "actiontable_short": [
    "CP20 0 0 > 1 OFF",
    "CP20 0 0 > 2 OFF",
    "CP20 0 0 > 3 OFF",
    "CP20 0 0 > 4 OFF",
    "CP20 0 1 > 1 ~ON",
    "CP20 0 1 > 2 ON",
    "CP20 0 1 > 3 ON",
    "CP20 0 1 > 4 ON"
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

### Service Layer

**File:** `src/xp/services/actiontable_service.py` *(existing)*

**Extend:** `ActionTableService`
- Add textual formatter methods

**Methods to implement:**
- `format_textual(actiontable: ActionTable) -> str`
- `format_entry_textual(entry: ActionTableEntry) -> str`

**Format logic:**
```python
def format_entry_textual(entry: ActionTableEntry) -> str:
    """Convert ActionTableEntry to textual format.

    Format: <Type> <Link> <Input> > <Output> <Command> <Parameter>
    Example: CP20 0 0 > 1 OFF
    """
    inverted = "~" if entry.inverted else ""
    param = f" {entry.parameter}" if entry.parameter else ""

    return (
        f"{entry.module_type} "
        f"{entry.link_number} "
        f"{entry.module_input} > "
        f"{entry.module_output} "
        f"{inverted}{entry.command}{param}"
    )
```

### CLI Layer

cli usage is not affected.
output has new informations

### Testing Layer

#### Unit Tests

**File:** `tests/unit/test_services/test_actiontable_service.py` *(existing)*

**Test methods:**
- `test_format_textual()`
- `test_format_entry_textual()`
- `test_format_entry_textual_with_inverted()`
- `test_format_entry_textual_with_parameter()`

**File:** `tests/unit/test_cli/test_conbus_actiontable_commands.py` *(existing)*

**Test methods:**
- `test_download_actiontable_format_text()`
- `test_download_actiontable_format_json()`
- `test_download_actiontable_format_default()`

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
CP20 0 0 > 1 OFF           # Normal OFF command
CP20 0 1 > 1 ~ON           # Inverted ON command
CP20 0 2 > 1 ON 500        # ON with 500ms parameter
XP24 1 3 > 2 TOGGLE        # TOGGLE on XP24 module
```

### Summary

Implementation adds textual format support to existing action table functionality:

1. **Extend service** - Add textual formatting methods
3. **No model changes** - Existing models work with both formats
4. **Test coverage** - Add format conversion test cases
5. **Backward compatible** - JSON remains default format

Benefits:
- Human-readable output
- Compatible with conson.yml configuration
- Easy copy/paste for configuration
- Matches documentation examples

## Quality
- run sh publish.sh --quality until all issues are fixed