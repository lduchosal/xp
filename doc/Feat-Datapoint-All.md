# Query all module datapoints

Use CLI to query all datapoints from a specific module

## CLI usage

Command:
```
xp conbus datapoint all <serial_number>
```

Output:
```json
{
  "success": true,
  "serial_number": "0123450001",
  "system_function": "02",
  "datapoints": [
    {  "DATAPOINT_NAME": "DATA_RAW_VALUE" },
    {  "AUTO_REPORT_STATUS": "AA" },
    {  "MODULE_STATE": "OFF" },
    {  "MODULE_OUTPUT_STATE": "xxxxx000" },
    {  "HW_VERSION": "XP33LED_HW_VER1" },
    {  "SW_VERSION": "XP33LED_V0.04.01" },
    {  "MODULE_LIGHT_LEVEL": "00:000[%],01:000[%],02:000[%]" }
  ],
  "error": null,
  "timestamp": "2025-09-26T08:54:13.876911"
}
```

**CLI checklist:**
- [ ] Add `datapoint` subcommand group to conbus group
- [ ] Add `all` subcommand to datapoint group with `<serial_number>` parameter
- [ ] Use conbus_datapoint_service to query module datapoints
- [ ] Add CLI command in `src/xp/cli/commands/conbus_datapoint_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer logic in service

## Service

`ConbusDatapointService` to handle module datapoint queries:

- Send appropriate telegrams to query all module datapoints
- Parse and validate datapoint responses
- Handle datapoint query error scenarios

Key methods:
- `query_all_datapoints(serial_number: str) -> ConbusDatapointResponse`

**Implementation checklist:**
- [ ] Create or reuse `ConbusDatapointService` class in `src/xp/services/conbus_datapoint_service.py`
- [ ] Define or reuse `ConbusDatapointResponse` model in `src/xp/models/conbus_datapoint.py`
- [ ] Use `ConbusService` to send datapoint query telegrams
- [ ] Use `TelegramDatapointService` to create appropriate telegram formats for datapoint queries
- [ ] Parse and validate telegram responses containing datapoint information
- [ ] Prefer composition to inheritance

## Tests

CLI integration tests in `tests/integration/test_conbus_datapoint_integration.py`:

- `test_conbus_datapoint_all_valid_serial()` - Test querying datapoints with valid serial number
- `test_conbus_datapoint_all_invalid_serial()` - Test with invalid serial number
- `test_conbus_datapoint_connection_error()` - Handle network failures
- `test_conbus_datapoint_invalid_response()` - Handle invalid responses

**Test checklist:**
- [ ] Test CLI command parsing and execution
- [ ] Test service datapoint query functionality
- [ ] Test error handling scenarios

## Quality checklist

**Linter:**
- [ ] Run `ruff check` to ensure code style compliance
- [ ] Fix any linting issues in CLI commands
- [ ] Fix any linting issues in service implementations
- [ ] Fix any linting issues in test files

**Typechecker:**
- [ ] Run `mypy` on all new code
- [ ] Ensure proper type annotations for all methods
- [ ] Fix any type checking errors in models
- [ ] Fix any type checking errors in services

**Tests:**
- [ ] Achieve minimum test coverage for new functionality
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test edge cases and error conditions

