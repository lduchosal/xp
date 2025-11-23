# Download Action Table

XP module's actiontable can be programme into the module flash memory

## cli

xp conbus actiontable download <serial_number>

### output
cli output
```
{
   module_type: ModuleTypeCode.XP20,
   link_number: 1,
   module_input: 1,
   module_output: 1.
   inverted: True,
   command: InputActionType.OFF,
   parameter: TimeParam.NONE
}

```

Decoded actiontable 

```
CP20 0 0 > 1 OFF; 
CP20 0 0 > 2 OFF;
CP20 0 0 > 3 OFF;
CP20 0 0 > 4 OFF;
CP20 0 1 > 1 ~ON;
CP20 0 1 > 2 ON;
CP20 0 1 > 3 ON;
CP20 0 1 > 4 ON;
```

Encoded actiontable

```
AAAAACAAAABAAAACAAAABBAAACAAAABCAAACAAAABDAAACAAABAIAAACAAABAJAAACAA
AAABABAKAAACAAABALAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAJAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAALAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAANAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
```

## actiontable definition

```
Format: 
<Type> <Link> <Input> > <Output> <Command> <Parameter>;
CP20 0 0 > 1 OFF; 

```
## Download protocol

```
[TX] <S0123450001F11D00FI> DOWNLOAD ACTION TABLE
[RX] <R0123450001F18DFA> ACK
[RX] <R0123450001F17DAAAAACAAAABAAAACAAAABBAAACAAAABCAAACAAAABDAAACAAABAIAAACAAABAJAAACAAFK> TABLE
[TX] <S0123450001F18D00FB> CONTINUE
[RX] <R0123450001F17DAAABABAKAAACAAABALAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFJ> TABLE
[TX] <S0123450001F18D00FB> CONTINUE
.
.
.
repeat until EOF
[RX] <R0123450001F16DFO> EOF
```

## Implementation Plan

### Service Layer

**File:** `src/xp/services/actiontable_service.py` *(new)*

**New service class:** `ActionTableService`
- Generic actiontable download service (not module-specific)
- Implements download protocol using F11D command
- Returns decoded actiontable data

**Methods to implement:**
- `download_actiontable(serial_number: str) -> ActionTable`
- `format_decoded_output(actiontable) -> str`
- `format_encoded_output(actiontable) -> str`

### CLI Layer

**File:** `src/xp/cli/commands/conbus_actiontable_commands.py` *(new)*

**New command:** `conbus_download_actiontable()`
- Generic actiontable download command (no module type required)
- Outputs both decoded and encoded formats

**Implementation:**
```python
@conbus_actiontable.command("download", short_help="Download ActionTable")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ActionTableError)
def conbus_download_actiontable(serial_number: str) -> None:
    """Download action table from XP module"""
    service = ActionTableService()

    with service:
        actiontable = service.download_actiontable(serial_number)
        output = {
            "serial_number": serial_number,
            "actiontable": asdict(actiontable),
        }

        click.echo(json.dumps(output, indent=2, default=str))

```

**CLI registration:** Add to `src/xp/cli/commands/conbus.py`

### Testing Layer

#### Unit Tests

**File:** `tests/unit/test_services/test_actiontable_service.py` *(new)*

**Test methods:**
- `test_format_decoded_output()`
- `test_format_encoded_output()`
- `test_download_actiontable_success()`
- `test_download_actiontable_communication_error()`

**File:** `tests/unit/test_cli/test_conbus_actiontable_commands.py` *(new)*

**Test methods:**
- `test_conbus_download_actiontable_success()`
- `test_conbus_download_actiontable_output_format()`
- `test_conbus_download_actiontable_error_handling()`

#### Integration Tests

**File:** `tests/integration/test_actiontable_integration.py` *(new)*

**Test methods:**
- `test_download_actiontable_integration()`
- `test_end_to_end_cli_download()`

### Model Layer Dependencies

**New model:** `src/xp/models/actiontable.py` *(new)*
- Generic ActionTable model
- Contains action entries in CP20 format

**New serializer:** `src/xp/services/actiontable_serializer.py` *(new)*
- Handles encoding/decoding of generic actiontable telegrams
- Converts between telegram format and ActionTable model

### Configuration Dependencies

**CLI integration** *(new)*:
- Register new command group in `src/xp/cli/commands/conbus.py`
- Available as: `xp conbus actiontable download <serial_number>`

### Summary

Implementation requires creating new generic actiontable functionality:

1. **New service** - Create `ActionTableService` for generic actiontables
2. **New CLI commands** - Create actiontable download command (no module type)
3. **New models** - Create generic `ActionTable` model and serializer
4. **Test coverage** - Add comprehensive unit and integration tests
5. **CLI integration** - Register new command group

Use existing conbus infrastructure and telegram protocols.

### Using Existing Infrastructure as Template

Use existing conbus services and commands as templates for implementation:

**models:** `src/xp/models/actiontable.py`
- ActionTableEntry
- ActionTable

**Service template:** `src/xp/services/conbus_service.py`
- Shows conbus protocol communication patterns
- Demonstrates telegram parsing and response handling
- Provides base infrastructure for F11D command

**Serializer template:** `src/xp/services/msactiontable_xp20_serializer.py`
- use msactiontable_xp20_serializer as template
- use Feat-Download-ActionTable.pseudocode.md as pseudo code guide

**CLI template:** `src/xp/cli/commands/conbus_*_commands.py`
- Shows command structure and argument handling
- Demonstrates error handling and service integration
- Use any conbus command as pattern reference

**Test templates:**
- Unit tests: `tests/unit/test_services/test_conbus_service.py`
- Integration tests: `tests/integration/test_*_integration.py`
- CLI tests: `tests/unit/test_cli/test_*_commands.py`

**Protocol reference:** `src/xp/services/msactiontable_download_service.py`
- Shows F13 download protocol (adapt for F11D)
- Demonstrates ACK/EOF handling patterns
- Provides telegram parsing examples

Use these existing files as reference for consistent code style, error handling patterns, and testing approaches.

## Quality
- run sh publish.sh --quality until all issues are fixed