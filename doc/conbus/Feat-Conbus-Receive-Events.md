# Conbus receive events telegrams

use cli to receive waiting event telegrams

## Cli usage

Command:
xp conbus receive

output:
```
<R2113010000F02D12>
<R2113010001F02D12>
<S2113010002F02D12>
<E12L1BAK>
```

**CLI checklist:**
- [ ] Add `receive` subcommand to conbus group
- [ ] use conbus_receive_service to receive telegrams
- [ ] Add CLI command in `src/xp/cli/commands/conbus_receive_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer logic in service

## Service

`ConbusReceiveService` to handle receive telegram sequences:

- Receive telegram via TCP connection
- no prior validation
- no received validation

Key methods:
- `receive_telegrams(receive_input: str) -> ConbusReceiveResponse`

**Implementation checklist:**
- [ ] Create `ConbusReceiveService` class in `src/xp/services/conbus_receive_service.py`
- [ ] Define `ConbusReceiveResponse` model in `src/xp/models/conbus_receive.py`
- [ ] Reuse `ConbusProtocol` send_receive_telegram() with empty str to receive telegrams

## Tests

CLI integration tests in `tests/integration/test_conbus_receive_integration.py`:

- `test_conbus_receive_single_telegram()` - Send single receive telegram
- `test_conbus_receive_multiple_telegrams()` - Send telegram sequence
- `test_conbus_receive_connection_error()` - Handle network failures

**Test checklist:**
- [ ] Test CLI command parsing and execution

