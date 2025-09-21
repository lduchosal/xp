# Feature: JSON-Only Output

## Overview
Convert CLI commands to output only JSON format by removing text output and the `--json-output` flag.

## Current State
- Commands support dual output modes via `--json-output` flag
- Text output includes formatted summaries, validation messages, and human-readable content
- JSON output provides structured data with consistent error handling

## Changes Required

### 1. Remove Text Output Logic
**Files to modify:**
- `src/xp/cli/commands/*.py` (all command files)

**Actions:**
- Remove all text output formatting code
- Keep only JSON response generation
- Remove conditional `if json_output:` blocks
- Ensure all responses use `click.echo(json.dumps(..., indent=2))`

### 2. Remove JSON Output Flag
**Files to modify:**
- `src/xp/cli/utils/decorators.py`

**Actions:**
- Remove `json_output_option` decorator
- Update all decorator functions to remove `json_output` parameter handling
- Remove `json_output` from function signatures

### 3. Update Command Functions
**Command categories to update:**
- Checksum commands (`checksum_commands.py`)
- Module commands (`module_commands.py`)
- Telegram commands (`telegram_commands.py`)
- Conbus commands (all `conbus_*.py` files)
- Server commands (`server_commands.py`)
- File commands (`file_commands.py`)
- Discover commands (`telegram_discover_commands.py`)

**Changes per command:**
- Remove `json_output: bool` parameter
- Remove text formatting logic
- Keep only JSON output with error handling

### 4. Update Error Handling
**Files to modify:**
- `src/xp/cli/utils/error_handlers.py`
- `src/xp/cli/utils/formatters.py`

**Actions:**
- Ensure all errors return JSON format
- Remove text-based error messages
- Maintain structured error responses

## Implementation Checklist

- [ ] Remove `json_output_option` decorator from `decorators.py`
- [ ] Update all command decorators to remove JSON flag handling
- [ ] Convert checksum commands to JSON-only output
- [ ] Convert module commands to JSON-only output
- [ ] Convert telegram parsing commands to JSON-only output
- [ ] Convert conbus operation commands to JSON-only output
- [ ] Convert server management commands to JSON-only output
- [ ] Convert file operation commands to JSON-only output
- [ ] Convert discover commands to JSON-only output
- [ ] Update error handlers for JSON-only responses
- [ ] Remove text formatters, keep JSON formatters
- [ ] Update all service command decorators
- [ ] Update connection command decorators
- [ ] Update file operation decorators

## Test Updates

### Tests to Modify
- `tests/unit/test_cli/test_conbus_blink_commands.py`
- All CLI command tests in `tests/unit/test_cli/`
- Integration tests in `tests/integration/`

### Test Changes
- Remove `--json-output` flag from test invocations
- Update assertions to expect JSON output only
- Remove text output validation tests
- Keep JSON structure validation tests
- Ensure error cases return proper JSON format

### New Tests to Add
- Verify all commands return valid JSON
- Verify consistent error JSON structure
- Verify no text output in any command

## Benefits
- Simplified CLI interface (no output format flag)
- Consistent structured output for automation
- Reduced code complexity in command implementations
- Better integration with external tools and scripts