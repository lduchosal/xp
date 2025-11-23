# Upload Action Table

Upload actiontable configuration from conson.yml to XP module's flash memory

## conson.yml Configuration

Add `action_table` field to module configuration:

```yaml
- name: A4
  serial_number: "0020044991"
  module_type: XP24
  module_type_code: 07
  link_number: 02
  module_number: 2
  auto_report_status: PP
  action_table:
    - CP20 0 0 > 1 OFF
    - CP20 0 0 > 2 OFF
    - CP20 0 0 > 3 OFF
    - CP20 0 0 > 4 OFF
    - CP20 0 1 > 1 ~ON
    - CP20 0 1 > 2 ON
    - CP20 0 1 > 3 ON
    - CP20 0 1 > 4 ON
```

## cli

xp conbus actiontable upload <serial_number>

### output
cli output
```
Uploading action table to 0020044991...
Action table uploaded successfully
8 entries written
```

## actiontable definition

```
Format:
<Type> <Link> <Input> > <Output> <Command> <Parameter>;
CP20 0 0 > 1 OFF;

```
## Upload protocol

```
1. [TX] <S{serial}F10D00{checksum}>         # Client: UPLOAD_ACTIONTABLE
2. [RX] <R{serial}F18D{checksum}>           # Module: ACK
4. [TX] <S{serial}F17D{data}{checksum}>     # Client: ACTIONTABLE
5. [RX] <R{serial}F18D00{checksum}>         # Client: CONTINUE
.
.
repeat until all entries sent
X. [TX] <S{serial}F16D{checksum}>           # Client: EOF
```

## Implementation Plan

### Service Layer

**File:** `src/xp/services/actiontable_service.py` *(existing)*

**Extend:** `ActionTableService`
- Add upload functionality to existing service
- Implements upload protocol using F10D command
- Reads actiontable from conson.yml configuration

**Methods to implement:**
- `upload_actiontable(serial_number: str, action_table: list[str]) -> bool`
- `encode_actiontable(action_table: list[str]) -> str`
- `validate_actiontable(action_table: list[str]) -> bool`

### CLI Layer

**File:** `src/xp/cli/commands/conbus_actiontable_commands.py` *(existing)*

**New command:** `conbus_upload_actiontable()`
- Reads action_table from conson.yml module configuration
- Validates and uploads to module

**Implementation:**
```python
@conbus_actiontable.command("upload", short_help="Upload ActionTable")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ActionTableError)
def conbus_upload_actiontable(serial_number: str) -> None:
    """Upload action table from conson.yml to XP module"""
    config = ConfigService.load_config()
    module = config.find_module(serial_number)

    if not module.action_table:
        raise ActionTableError(f"No action_table configured for {serial_number}")

    service = ActionTableService()

    with service:
        service.upload_actiontable(serial_number, module.action_table)
        click.echo(f"Action table uploaded successfully")
        click.echo(f"{len(module.action_table)} entries written")

```

**CLI registration:** Add to existing `src/xp/cli/commands/conbus.py`

### Testing Layer

#### Unit Tests

**File:** `tests/unit/test_services/test_actiontable_service.py` *(existing)*

**Test methods:**
- `test_encode_actiontable()`
- `test_validate_actiontable()`
- `test_upload_actiontable_success()`
- `test_upload_actiontable_invalid_format()`
- `test_upload_actiontable_communication_error()`

**File:** `tests/unit/test_cli/test_conbus_actiontable_commands.py` *(existing)*

**Test methods:**
- `test_conbus_upload_actiontable_success()`
- `test_conbus_upload_actiontable_missing_config()`
- `test_conbus_upload_actiontable_error_handling()`

#### Integration Tests

**File:** `tests/integration/test_actiontable_integration.py` *(existing)*

**Test methods:**
- `test_upload_actiontable_integration()`
- `test_end_to_end_cli_upload()`
- `test_upload_download_roundtrip()`

### Model Layer Dependencies

**Extend model:** `src/xp/models/conson.py` *(existing)*
- Add `action_table: Optional[list[str]]` field to module configuration
- Add validation for action_table format

**Extend serializer:** `src/xp/services/actiontable_serializer.py` *(existing)*
- Add encoding logic for upload telegrams
- Add validation for action table entries

### Configuration Dependencies

**CLI integration** *(existing)*:
- Extend command group in `src/xp/cli/commands/conbus.py`
- Available as: `xp conbus actiontable upload <serial_number>`

**Configuration** *(new)*:
- conson.yml schema update to support `action_table` field

### Summary

Implementation extends existing actiontable functionality:

1. **Extend service** - Add upload methods to `ActionTableService`
2. **New CLI command** - Create upload command that reads from conson.yml
3. **Extend models** - Add action_table field to module configuration
4. **Test coverage** - Add upload test cases to existing test files
5. **CLI integration** - Register upload command in existing group

Use existing download implementation as reference for protocol patterns.

### Using Existing Infrastructure as Template

**Service template:** `src/xp/services/actiontable_service.py`
- Mirror download protocol for upload (F10D vs F11D)
- Reuse existing serializer for encoding

**Serializer template:** `src/xp/services/actiontable_serializer.py`
- Use existing decode logic as reference for encode
- Maintain consistent telegram format

**CLI template:** `src/xp/cli/commands/conbus_actiontable_commands.py`
- Follow download command pattern
- Add configuration reading logic

**Protocol reference:** `src/xp/services/msactiontable_download_service.py`
- Shows F10D upload protocol (adapt for F11D)
- Demonstrates telegram chunking patterns

## Quality
- run sh publish.sh --quality until all issues are fixed