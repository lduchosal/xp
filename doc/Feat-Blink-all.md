# Conbus blink all commands

Use CLI to control all device blinking states

## Cli usage

Commands:
```
xp conbus blink all off
xp conbus blink all on
```

Output:
```
All devices blink turned off
All devices blink turned on
```

**CLI checklist:**
- [ ] Add `blink` subcommand group to conbus group
- [ ] Add `all` subcommand to blink group with `off` and `on` actions
- [ ] Use conbus_blink_service to control device blinking
- [ ] Add CLI command in `src/xp/cli/commands/conbus_blink_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer logic in service

## Service

`ConbusBlinkService` to handle device blink control:

- Send appropriate telegrams to control all device blinking
- Handle blink on/off state management
- Validate blink command responses

Key methods:
- `blink_all_off() -> ConbusBlinkResponse`
- `blink_all_on() -> ConbusBlinkResponse`

**Implementation checklist:**
- [ ] Create or reuse `ConbusBlinkService` class in `src/xp/services/conbus_blink_service.py`
- [ ] Define or reuse `ConbusBlinkResponse` model in `src/xp/models/conbus_blink.py`
- [ ] Reuse `ConbusBlinkService` to send blink control telegrams
- [ ] Reuse `ConbusDiscoverService` to list discovered_devices
- [ ] Iterate through discovered_devices and prepare multiple telegrams and send them all at once using `ConbusService` `send_raw_telegram`  
- [ ] Reuse `TelegramBlinkService` to create appropriate telegram formats for blink all on/off commands
- [ ] prefer composition to inheritance

## Tests

CLI integration tests in `tests/integration/test_conbus_blink_integration.py`:

- `test_conbus_blink_all_off()` - Test turning all device blinks off
- `test_conbus_blink_all_on()` - Test turning all device blinks on
- `test_conbus_blink_connection_error()` - Handle network failures
- `test_conbus_blink_invalid_response()` - Handle invalid responses

**Test checklist:**
- [ ] Test CLI command parsing and execution
- [ ] Test service blink control functionality
- [ ] Test error handling scenarios