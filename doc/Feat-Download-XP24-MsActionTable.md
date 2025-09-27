# XP24 MS Action Table Download Feature

XP24 module's action table can be programmed into the module flash memory. This feature enables downloading and uploading action tables that define how inputs respond to events.

## CLI Usage

### Download Action Table
```bash
xp conbus msactiontable download <serial_number> [decode (default true)]
```

### Example Output

```json
{
  "serial_number": "0123450001",
  "action_table": {
    "input1_action": {
      "type": "TOGGLE",
      "param": null
    },
    "input2_action": {
      "type": "TOGGLE",
      "param": null
    },
    "input3_action": {
      "type": "TOGGLE",
      "param": null
    },
    "input4_action": {
      "type": "TOGGLE",
      "param": null
    },
    "mutex12": false,
    "mutex34": false,
    "curtain12": false,
    "curtain34": false,
    "ms": 12
  },
  "raw": "AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
}
```

## Protocol Communication

### Download Sequence
```
[TX] <S0123450001F13D00FK>   DOWNLOAD MS ACTION TABLE REQUEST
[RX] <R0123450001F18DFA>     ACK
[RX] <R0123450001F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>   TABLE DATA
[TX] <S0123450001F18D00FB>   CONTINUE
[RX] <R0123450001F16DFO>     EOF
```

### Telegram Format

#### MS Action Table Query (F13)
```
<S{serial}F13D00{checksum}>
```

#### MS Action Table Response (F17)
```
<S{serial}F17DAAAA{4_rows}{mutex12}{mutex34}{ms}{curtain12}{curtain34}{padding}{checksum}>
```

Where:
- `{4_rows}`: 8 bytes (4 rows × 2 bytes per row: function_id + parameter_id)
- `{mutex12}`: AA/AB (mutex for inputs 1-2)
- `{mutex34}`: AA/AB (mutex for inputs 3-4)
- `{ms}`: Timing value (MS300=12, MS500=20)
- `{curtain12}`: AA/AB (curtain setting for inputs 1-2)
- `{curtain34}`: AA/AB (curtain setting for inputs 3-4)
- `{padding}`: 19 bytes of "AA" padding

## Python Implementation

see Feat-Download-XP24-MsActionTable.pseudo.md

## Tests

CLI integration tests in `tests/integration/test_xp24_action_table_integration.py`:

- `test_xp24_download_action_table()` - Test downloading action table from module
- `test_xp24_upload_action_table()` - Test uploading action table to module
- `test_xp24_action_table_serialization()` - Test telegram encoding/decoding
- `test_xp24_action_table_invalid_serial()` - Test invalid serial number handling
- `test_xp24_action_table_connection_error()` - Test network failure handling
- `test_xp24_action_table_invalid_response()` - Test invalid telegram response

Unit tests in `tests/unit/test_models/test_xp24_action_table.py`:

- `test_xp24_action_table_creation()` - Test dataclass instantiation
- `test_xp24_action_table_defaults()` - Test default values
- `test_input_action_type_enum()` - Test all action type values
- `test_xp24_action_table_constants()` - Test MS300/MS500 constants

Unit tests in `tests/unit/test_services/test_xp24_action_table_service.py`:

- `test_xp24_action_table_serializer_to_telegrams()` - Test telegram generation
- `test_xp24_action_table_serializer_from_telegrams()` - Test telegram parsing
- `test_xp24_action_table_service_download()` - Test service download functionality
- `test_xp24_action_table_service_upload()` - Test service upload functionality
- `test_xp24_action_table_checksum_calculation()` - Test checksum handling

**Test checklist:**
- [ ] Test CLI command parsing and execution
- [ ] Test service action table download/upload functionality
- [ ] Test telegram serialization and deserialization
- [ ] Test error handling scenarios (network failures, invalid responses)
- [ ] Test all InputActionType enum values
- [ ] Test dataclass field validation and defaults
- [ ] Test checksum calculation and validation

## Quality

- [ ] pdm run typecheck "Type checking"
- [ ] pdm run refurb "Code quality check"
- [ ] pdm run lint "Linting"
- [ ] pdm run format "Code formatting"
- [ ] pdm run vulture "Dead code check"
- [ ] pdm run test-quick "Tests"
- [ ] sh publish.sh --quality
 