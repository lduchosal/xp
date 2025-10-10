# Conbus lightlevel commands

Use CLI to control light level (dimming) of outputs on Conbus modules

## Cli usage

Commands:
```
xp conbus lightlevel set <serial_number> <output_number> <level>
xp conbus lightlevel off <serial_number> <output_number>
xp conbus lightlevel on <serial_number> <output_number>
xp conbus lightlevel get <serial_number> <output_number>
```

Example:
```
xp conbus lightlevel set 0123450001 02 050
```

Output:
```
set the light level to 50% for output_number 2 of module 0123450001
sent telegram <S0123450001F04D1502:050FN>
received reply <R0123450001F18DFI> ACK
event sent <E35L15I82MAF> Make (on)
```

**CLI checklist:**
- [ ] Add `lightlevel` subcommand group to conbus group
- [ ] Add `set` subcommand with `serial_number`, `output_number`, and `level` parameters
- [ ] Add `off` subcommand (equivalent to set level 0)
- [ ] Add `on` subcommand (equivalent to set level 80)
- [ ] Add `get` subcommand to query current light level
- [ ] Use conbus_lightlevel_service to control light levels
- [ ] Add CLI command in `src/xp/cli/commands/conbus_lightlevel_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer logic in service
- [ ] Use colored click options

## Service

`ConbusLightlevelService` to handle light level control:

- Send appropriate telegrams to control output light levels
- Handle light level state management (0-100%)
- Validate light level command responses
- Generate appropriate events

Key methods:
- `set_lightlevel(serial_number, output_number, level) -> ConbusLightlevelResponse`
- `turn_off(serial_number, output_number) -> ConbusLightlevelResponse`
- `turn_on(serial_number, output_number) -> ConbusLightlevelResponse`
- `get_lightlevel(serial_number, output_number) -> ConbusLightlevelResponse`

**Implementation checklist:**
- [ ] Create `ConbusLightlevelService` class in `src/xp/services/conbus_lightlevel_service.py`
- [ ] Define `ConbusLightlevelResponse` model in `src/xp/models/conbus_lightlevel.py`
- [ ] Use `ConbusService` to send lightlevel control telegrams
- [ ] Create or reuse `TelegramLightlevelService` to build appropriate telegram formats
- [ ] Validate light level range (0-100)
- [ ] Handle telegram responses
- [ ] Prefer composition to inheritance

## Tests

CLI integration tests in `tests/integration/test_conbus_lightlevel_integration.py`:

- `test_conbus_lightlevel_set()` - Test setting specific light level
- `test_conbus_lightlevel_off()` - Test turning light off (level 0)
- `test_conbus_lightlevel_on()` - Test turning light on (level 80)
- `test_conbus_lightlevel_get()` - Test querying light level
- `test_conbus_lightlevel_invalid_level()` - Test invalid level values
- `test_conbus_lightlevel_connection_error()` - Handle network failures
- `test_conbus_lightlevel_invalid_response()` - Handle invalid responses

**Test checklist:**
- [ ] Test CLI command parsing and execution
- [ ] Test service light level control functionality
- [ ] Test error handling scenarios
- [ ] Test telegram format validation

### Quality

- [ ] pdm run typecheck "Type checking"
- [ ] pdm run refurb "Code quality check"
- [ ] pdm run lint "Linting"
- [ ] pdm run format "Code formatting"
- [ ] pdm run vulture "Dead code check"
- [ ] pdm run test-quick "Tests"
 