# Conbus raw telegrams

use cli to send raw and multiple telegrams to the conbus

## Cli usage

Command:
xp conbus raw '\<S2113010000F02D12>\<S2113010001F02D12>\<S2113010002F02D12>'

output:
```
<R2113010000F02D12>
<R2113010001F02D12>
<S2113010002F02D12>
```

**CLI checklist:**
- [ ] Add `raw` subcommand to conbus group
- [ ] Accept raw telegram string as argument
- [ ] use conbus_raw_service to send telegrams
- [ ] Add CLI command in `src/xp/cli/commands/conbus_raw_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer put logic in service

## Service

`ConbusRawService` to handle raw telegram sequences:

- Send raw parameter telegram via TCP connection
- no prior validation
- no received validation

Key methods:
- `send_raw_telegrams(raw_input: str) -> ConbusRawResponse`
- `parse_telegram_sequence(input: str) -> List[str]`

**Implementation checklist:**
- [ ] Create `ConbusRawService` class in `src/xp/services/conbus_raw_service.py`
- [ ] Define `ConbusRawResponse` model in `src/xp/models/conbus_raw.py`
- [ ] Reuse `ConbusService` to send raw telegrams

## Tests

CLI integration tests in `tests/integration/test_conbus_raw_integration.py`:

- `test_conbus_raw_single_telegram()` - Send single raw telegram
- `test_conbus_raw_multiple_telegrams()` - Send telegram sequence
- `test_conbus_raw_connection_error()` - Handle network failures

**Test checklist:**
- [ ] Test CLI command parsing and execution
