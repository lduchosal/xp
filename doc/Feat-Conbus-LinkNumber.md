# Set link number to a module

Use CLI to set the link number for a specific module

## CLI usage

Command:
```
xp conbus linknumber <serial_number> <link_number>
```

Output:
```
{
  "success": true,
  "link_number": "04",
  "result": "ACK",
  "serial_number": "0020045057",
  "sent_telegram": "<S0020045057F02D04FG>",
  "received_telegrams": [
    "<R0020045057F02D0400FH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383",
}
```

**CLI checklist:**
- [ ] Add `linknumber` subcommand to conbus group
- [ ] Accept `serial_number` argument with `type=SERIAL` for validation
- [ ] Accept `link_number` argument with `type=click.IntRange(0, 99)` for validation
- [ ] Use conbus_linknumber_service to set module link number
- [ ] Add CLI command in `src/xp/cli/commands/conbus_linknumber_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer logic in service

## Service

`ConbusLinknumberService` to handle module link number assignment:

- Send appropriate telegrams to set module link numbers
- Handle link number assignment validation
- Validate link number command responses

Key methods:
- `set_linknumber(serial_number: str, link_number: int) -> ConbusLinknumberResponse`

**Implementation checklist:**
- [ ] Create or reuse `ConbusLinknumberService` class in `src/xp/services/conbus_linknumber_service.py`
- [ ] Define or reuse `ConbusLinknumberResponse` model in `src/xp/models/conbus_linknumber.py`
- [ ] Reuse `ConbusLinknumberService` to send link number assignment telegrams
- [ ] Reuse `LinkNumberService` (from `telegram_link_number_service`) to create appropriate telegram formats
- [ ] Use `ConbusService` `send_raw_telegram` for telegram transmission
- [ ] Link number validation handled by Click IntRange (0-99)
- [ ] Serial number validation handled by SERIAL type
- [ ] Prefer composition to inheritance

## Tests

CLI integration tests in `tests/integration/test_conbus_linknumber_integration.py`:

- `test_conbus_linknumber_valid()` - Test setting valid link number
- `test_conbus_linknumber_invalid_response()` - Handle invalid responses

**Test checklist:**
- [ ] Test CLI command parsing and execution
- [ ] Test service link number assignment functionality
- [ ] Test error handling scenarios

## Quality

**Quality assurance checklist:**
- [ ] Run `pdm run typecheck` - Type checking passes
- [ ] Run `pdm run lint` - Linting passes
- [ ] Run `pdm run test-unit` - Unit tests pass
- [ ] Run `pdm run test-integration` - Integration tests pass
- [ ] Run `pdm run test` - Full test suite with coverage
- [ ] Code coverage meets requirements (60%+)
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Input validation added

