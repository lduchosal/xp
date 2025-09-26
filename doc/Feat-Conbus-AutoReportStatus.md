# Auto Report Status Management for modules

Use CLI to get and set the auto report status for specific modules

## CLI usage

### Get auto report status
Command:
```
xp conbus autoreport get <serial_number>
```

Output:
```
{
  "success": true,
  "serial_number": "0123450001",
  "auto_report_status": "AA",
  "sent_telegram": "<S0123450001F02D21FG>",
  "received_telegrams": [
    "<R0123450001F02D21AAFH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383"
}
```

### Set auto report status ON
Command:
```
xp conbus autoreport set <serial_number> on
```

Output:
```
{
  "success": true,
  "serial_number": "0123450001",
  "auto_report_status": "on",
  "result": "ACK",
  "sent_telegram": "<S0123450001F04E21PPFG>",
  "received_telegrams": [
    "<R0123450001F18DFH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383"
}
```

### Set auto report status OFF
Command:
```
xp conbus autoreport set <serial_number> off
```

Output:
```
{
  "success": true,
  "serial_number": "0123450001",
  "auto_report_status": "off",
  "result": "ACK",
  "sent_telegram": "<S0123450001F04E21AAFG>",
  "received_telegrams": [
    "<R0123450001F18DFH>"
  ],
  "error": null,
  "timestamp": "2025-09-26T13:11:25.820383"
}
```

**CLI checklist:**
- [ ] Add `autoreport` subcommand group to conbus group
- [ ] Add `get` subcommand with `<serial_number>` parameter
- [ ] Add `set` subcommand with `<serial_number>` and `<on|off>` parameters
- [ ] Use autoreport service to get/set module auto report status
- [ ] Add CLI command in `src/xp/cli/commands/conbus_autoreport_commands.py`
- [ ] Register command in `src/xp/cli/commands/conbus.py`
- [ ] As few as possible logic in cli, prefer logic in service

## Service

`ConbusAutoreportService` to handle module auto report status operations:

- Send appropriate telegrams to get current auto report status
- Send telegrams to set auto report status (on/off)
- Parse and validate auto report responses
- Handle auto report operation error scenarios

Key methods:
- `get_autoreport_status(serial_number: str) -> ConbusAutoreportResponse`
- `set_autoreport_status(serial_number: str, status: bool) -> ConbusAutoreportResponse`

**Implementation checklist:**
- [ ] Create `ConbusAutoreportService` class in `src/xp/services/conbus_autoreport_service.py`
- [ ] Define `ConbusAutoreportResponse` model in `src/xp/models/conbus_autoreport.py`
- [ ] Use `ConbusService` to send autoreport query/set telegrams
- [ ] Use `TelegramService` to parse reply telegrams containing autoreport information
- [ ] Use `SystemFunction.READ_DATAPOINT` for get operations
- [ ] Use `SystemFunction.WRITE_DATAPOINT` for set operations
- [ ] Use `DataPointType.AUTO_REPORT_STATUS` for datapoint identification
- [ ] Serial number validation handled by SERIAL type
- [ ] Boolean status parameter validation for on/off operations
- [ ] Prefer composition to inheritance

## Models

`DataPointType` enum defines the auto report status datapoint:

```python
AUTO_REPORT_STATUS = "21"  # Auto Report Status
```

The datapoint code "21" is used in telegram construction to query the auto report status from modules.

**Model checklist:**
- [x] Define `AUTO_REPORT_STATUS = "21"` in `DataPointType` enum
- [x] Support auto report status in datapoint type choice validation
- [x] Include auto report status in CLI help and documentation

## Tests

CLI integration tests in `tests/integration/test_conbus_autoreport_integration.py`:

- `test_conbus_autoreport_get_valid_serial()` - Test getting auto report status with valid serial
- `test_conbus_autoreport_set_on_valid_serial()` - Test setting auto report status to ON
- `test_conbus_autoreport_set_off_valid_serial()` - Test setting auto report status to OFF
- `test_conbus_autoreport_invalid_serial()` - Test with invalid serial number
- `test_conbus_autoreport_connection_error()` - Handle network failures
- `test_conbus_autoreport_invalid_response()` - Handle invalid responses

**Test checklist:**
- [ ] Test CLI command parsing and execution for get/set operations
- [ ] Test service autoreport get functionality
- [ ] Test service autoreport set functionality with on/off values
- [ ] Test error handling scenarios
- [ ] Test serial number validation
- [ ] Test boolean parameter validation for set operations

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

## Usage Examples

Get auto report status from a specific module:
```bash
xp conbus autoreport get 0123450001
```

Set auto report status to ON for a module:
```bash
xp conbus autoreport set 0123450001 on
```

Set auto report status to OFF for a module:
```bash
xp conbus autoreport set 0123450001 off
```

The auto report status controls whether the module automatically reports status changes without being polled.