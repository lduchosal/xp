# MsActionTable Upload

Upload msactiontable configuration from conson.yml to XP module flash memory

## conson.yml Configuration

Add `xpXX_msaction_table` field to module configuration:

```yaml
- name: A4
  serial_number: "0020044991"
  module_type: XP24
  module_type_code: 07
  link_number: 02
  module_number: 2
  auto_report_status: PP
  xp24_msaction_table:
    - T:1 T:2 ON:0 OF:0 | M12:0 M34:0 C12:0 C34:0 DT:12
```

## CLI

```bash
xp conbus msactiontable upload <serial_number> <xpmoduletype>
```

### Output

```
Uploading msactiontable to 0020044991...
.
Msactiontable uploaded successfully
```

## Upload Protocol

MsActionTable is short enough to send in a single chunk (68 characters: AAAA fixed header + 64 data chars).

```
1. [TX] <S{serial}F12D00{checksum}>         # Client: UPLOAD_MSACTIONTABLE
2. [RX] <R{serial}F18D{checksum}>           # Module: ACK
3. [TX] <S{serial}F17D{data}{checksum}>     # Client: MSACTIONTABLE (single chunk, 68 chars)
4. [RX] <R{serial}F18D00{checksum}>         # Module: ACK
5. [TX] <S{serial}F16D{checksum}>           # Client: EOF
```

**Data format:** AAAA (fixed header) + 64 characters (32 bytes encoded as A-P nibbles)

## Implementation Checklist

### Service Layer

- [ ] Create `MsActionTableUploadService`
  - [ ] File: `src/xp/services/conbus/msactiontable/msactiontable_upload_service.py`
  - [ ] Signal-based architecture using `ConbusEventProtocol`
  - [ ] Support XP20, XP24, XP33 module types
  - [ ] Context manager pattern for singleton reuse
  - [ ] Event handlers: `connection_made`, `telegram_sent`, `telegram_received`, `timeout`, `failed`
  - [ ] Signals: `on_progress`, `on_error`, `on_finish`

### Service Methods

- [ ] `__init__(conbus_protocol, xp20ms_serializer, xp24ms_serializer, xp33ms_serializer, telegram_service, conson_config)`
- [ ] `connection_made()` - Send F12D UPLOAD_MSACTIONTABLE telegram
- [ ] `telegram_sent(telegram_sent)` - Log sent telegram
- [ ] `telegram_received(telegram_received)` - Handle ACK/NAK responses
- [ ] `_handle_upload_response(reply_telegram)` - Send data chunk or EOF
- [ ] `timeout()` - Handle timeout failure
- [ ] `failed(message)` - Emit error signal
- [ ] `start(serial_number, xpmoduletype, timeout_seconds)` - Setup upload parameters
- [ ] `set_timeout(timeout_seconds)` - Configure timeout
- [ ] `start_reactor()` / `stop_reactor()` - Reactor lifecycle
- [ ] `__enter__()` / `__exit__()` - Context manager with signal cleanup

### Upload State Management

- [ ] Store serializer based on module type (xp20/xp24/xp33)
- [ ] Read msactiontable from conson.yml via `ConsonModuleListConfig` (injected via DI)
- [ ] Extract first element from config list field (e.g., `module.xp24_msaction_table[0]`)
- [ ] Parse short format string to model using `XpXXMsActionTable.from_short_format()`
- [ ] Serialize model to telegram data using `XpXXMsActionTableSerializer.to_encoded_string()`
- [ ] Store single 68-character data chunk (no chunking needed)
- [ ] Track upload state: send data chunk after first ACK, then EOF
- [ ] Reset state in `__enter__()` for singleton reuse

### CLI Layer

- [ ] Add `upload` command to `conbus_msactiontable` group
  - [ ] File: `src/xp/cli/commands/conbus/conbus_msactiontable_commands.py`
  - [ ] Accept `serial_number` and `xpmoduletype` arguments
  - [ ] Read module config from conson.yml via injected service
  - [ ] Validate module's `module_type` matches `xpmoduletype` argument
  - [ ] Validate correct msactiontable field exists (e.g., `xp24_msaction_table` for XP24)
  - [ ] Progress indicator: show dots (`.`) during upload
  - [ ] Success/error message output

### CLI Command Structure

```python
@conbus_msactiontable.command("upload")
@click.argument("serial_number", type=SERIAL)
@click.argument("xpmoduletype", type=XP_MODULE_TYPE)
def conbus_upload_msactiontable(serial_number: str, xpmoduletype: str) -> None:
    """Upload msactiontable from conson.yml to XP module"""
```

### Configuration Integration

- [ ] Support `xp20_msaction_table` field in conson.yml (single-element list)
- [ ] Support `xp24_msaction_table` field in conson.yml (single-element list)
- [ ] Support `xp33_msaction_table` field in conson.yml (single-element list)
- [ ] Read short format string from config (first element of list)
- [ ] Validate `xpmoduletype` argument matches module's `module_type` field
- [ ] Validate correct msactiontable field exists for module type (e.g., XP24 requires `xp24_msaction_table`)

### Serializer Integration

- [ ] Use `Xp20MsActionTableSerializer.to_encoded_string()` for encoding
- [ ] Use `Xp24MsActionTableSerializer.to_encoded_string()` for encoding
- [ ] Use `Xp33MsActionTableSerializer.to_encoded_string()` for encoding
- [ ] Use `XpXXMsActionTable.from_short_format()` for parsing
- [ ] 68-character telegram data format (AAAA + 64 chars)

### Testing

- [ ] Unit tests: `tests/unit/test_services/test_msactiontable_upload_service.py`
  - [ ] `test_upload_xp20_msactiontable_success()`
  - [ ] `test_upload_xp24_msactiontable_success()`
  - [ ] `test_upload_xp33_msactiontable_success()`
  - [ ] `test_upload_invalid_format()`
  - [ ] `test_upload_communication_error()`
  - [ ] `test_upload_timeout()`
  - [ ] `test_upload_nak_response()`
  - [ ] `test_upload_missing_config()`
  - [ ] `test_upload_unsupported_module_type()`

- [ ] CLI tests: `tests/unit/test_cli/test_conbus_msactiontable_commands.py`
  - [ ] `test_upload_msactiontable_success()`
  - [ ] `test_upload_missing_config()`
  - [ ] `test_upload_module_type_mismatch()`
  - [ ] `test_upload_wrong_module_type_field()`
  - [ ] `test_upload_empty_msactiontable_list()`
  - [ ] `test_upload_error_handling()`

- [ ] Integration tests: `tests/integration/test_msactiontable_integration.py`
  - [ ] `test_upload_msactiontable_integration()`
  - [ ] `test_end_to_end_cli_upload()`
  - [ ] `test_upload_download_roundtrip()`

### Error Handling

- [ ] Module not found in conson.yml
- [ ] Module type mismatch: `xpmoduletype` arg doesn't match module's `module_type` field
- [ ] Missing msactiontable field in config for module type (e.g., XP24 but no `xp24_msaction_table`)
- [ ] Wrong msactiontable field for module type (e.g., XP24 with `xp20_msaction_table`)
- [ ] Empty msactiontable list in config
- [ ] Invalid short format syntax in config string
- [ ] Unsupported module type
- [ ] Communication timeout
- [ ] NAK response from module
- [ ] Invalid telegram response

### Dependencies

- [ ] `ConbusEventProtocol` for communication
- [ ] `Xp20MsActionTableSerializer` for XP20 encoding
- [ ] `Xp24MsActionTableSerializer` for XP24 encoding
- [ ] `Xp33MsActionTableSerializer` for XP33 encoding
- [ ] `TelegramService` for telegram parsing
- [ ] `ConsonModuleListConfig` for config access
- [ ] `SystemFunction.UPLOAD_MSACTIONTABLE` (F12D)
- [ ] `SystemFunction.MSACTIONTABLE` (F17D)
- [ ] `SystemFunction.ACK` (F18D)
- [ ] `SystemFunction.EOF` (F16D)

## Quality

- [ ] pdm run typecheck
- [ ] pdm run refurb
- [ ] pdm run lint
- [ ] pdm run format
- [ ] pdm run vulture
- [ ] pdm run test-quick
- [ ] sh publish.sh --quality