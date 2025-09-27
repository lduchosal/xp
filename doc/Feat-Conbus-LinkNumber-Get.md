# Get link number of a module

Use CLI to get the current link number for a specific module

## CLI usage

Command:
```
xp conbus linknumber get <serial_number>
```

Output:
```
{
  "success": true,
  "link_number": 10,
  "serial_number": "0123450001",
  "sent_telegram": "<S0123450001F03D04FG>",
  "received_telegrams": [
    "<R0123450001F03D040AFH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383"
}
```

**Implementation Checklist:**

## CLI Command
- [ ] Add `get` subcommand to existing linknumber command group
- [ ] Accept `serial_number` argument with `type=SERIAL` for validation
- [ ] Use ConbusLinknumberService to read module link number
- [ ] Add CLI command as subcommand in `src/xp/cli/commands/conbus_linknumber_commands.py`
- [ ] Minimal logic in CLI, delegate to service

## Service Enhancement
- [ ] Add `get_linknumber(serial_number: str) -> ConbusLinknumberResponse` method to existing `ConbusLinknumberService`
- [ ] Reuse existing `ConbusDatapointService.query_datapoint()` with `DataPointType.LINK_NUMBER`
- [ ] Parse response to extract link number from datapoint query result
- [ ] Update `ConbusLinknumberResponse` model to include optional `link_number` field
- [ ] Handle datapoint responses appropriately

## Tests
- [ ] Add unit tests for `get_linknumber()` method
- [ ] Add integration tests for get command functionality
- [ ] Test error handling for invalid responses and connection failures

## Model Update
- [ ] Add optional `link_number: Optional[int]` field to `ConbusLinknumberResponse`
- [ ] Update `to_dict()` method to include link_number field

## Quality
- [ ] Run `pdm run typecheck` - Type checking passes
- [ ] Run `pdm run lint` - Linting passes
- [ ] Run `pdm run test-unit` - Unit tests pass
- [ ] Run `pdm run test-integration` - Integration tests pass
- [ ] Run `pdm run test` - Full test suite with coverage
- [ ] Code coverage meets requirements (60%+)

