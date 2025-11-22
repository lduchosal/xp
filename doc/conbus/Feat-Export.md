# Conbus Export Feature

## Overview

Export complete device configuration from Conbus network to YAML file. Discovers all devices and queries their configuration datapoints to generate a structured export file compatible with `conson.yml` format.

## Problem Statement

Currently, creating `conson.yml` configuration requires manual device discovery and datapoint queries. This is time-consuming and error-prone when setting up new systems or documenting existing installations.

## Solution

Automated export command that:
1. Discovers all devices on the Conbus network
2. Queries configuration datapoints for each device
3. Generates complete `export.yml` in `conson.yml` format

## Use Cases

- **Initial Setup**: Export existing installation to create baseline configuration
- **Documentation**: Generate accurate device inventory
- **Migration**: Export configuration from one system to import into another
- **Backup**: Snapshot current network state

## Output Format

Export file matches `ConsonModuleListConfig` structure:

```yaml
root:
  - serial_number: "0020041013"
    module_type: XP130
    module_type_code: 13
    link_number: 12
    module_number: 1
    sw_version: XP130_V0.10.04
    hw_version: XP130_HW_Rev B
    auto_report_status: AA
    action_table: 
      - table 1
      - table 2

  - serial_number: "1234567890"
    module_type: XP24
    module_type_code: 7
    link_number: 9
    module_number: 2
    sw_version: XP24_V0.34.03
    hw_version: XP24_HW_Rev C
    auto_report_status: PP
```

## CLI Interface

```bash
# Export to default file (export.yml)
xp conbus export
```

### Command Options

none

## Implementation Approach

### Event-Driven Flow

Following `ConbusDiscoverService` pattern:

**1. Initialization**
- Inject `ConbusEventProtocol` via constructor
- Connect protocol signals to service handlers in `__init__`
- Initialize internal state (device queue, current device, export data)

**2. Connection Established** (`connection_made`)
- Send DISCOVERY telegram (serial "0000000000", function F01D)
- Start timeout timer
- Wait for device responses

**3. Telegram Received** (`telegram_received`)
- **Discovery Response** (F01D): Add serial to device queue, send first datapoint query
- **Datapoint Response** (F02D): Store value, query next datapoint or next device
- Parse telegram type and payload to determine response type
- Update internal state for current device being queried

**4. Datapoint Query Sequence** (per device)
- Query MODULE_TYPE_CODE → store code
- Query MODULE_TYPE → store type string
- Query LINK_NUMBER → store link
- Query MODULE_NUMBER → store number
- Query SOFTWARE_VERSION → store version
- Query HARDWARE_VERSION → store hw version
- Query AUTO_REPORT → store status
- When complete: emit `on_device_exported`, query next device

**5. Finalization** (`timeout` or all devices complete)
- Build `ConsonModuleListConfig` from collected data
- Serialize to YAML
- Write to output file
- Emit `on_finish` with result

**6. Cleanup** (`__exit__`)
- Disconnect all protocol signals
- Stop reactor
- Clear internal state

### State Management

Service maintains:
- `device_queue: List[str]` - Serial numbers to query
- `current_device: Optional[str]` - Device being queried
- `current_datapoint_index: int` - Which datapoint to query next
- `device_configs: Dict[str, ConsonModuleConfig]` - Collected configs
- `export_result: ConbusExportResponse` - Final result

### Data Models

**Request Model** (internal state)
```python
datapoint_sequence = [
    DataPointType.MODULE_TYPE_CODE,
    DataPointType.MODULE_TYPE,
    DataPointType.LINK_NUMBER,
    DataPointType.MODULE_NUMBER,
    DataPointType.SOFTWARE_VERSION,
    DataPointType.HARDWARE_VERSION,
    DataPointType.AUTO_REPORT,
]
```

**Response Model** (Pydantic)
```python
@dataclass
class ConbusExportResponse:
    success: bool
    config: Optional[ConsonModuleListConfig] = None
    device_count: int = 0
    output_file: Optional[str] = None
    error: Optional[str] = None
    sent_telegrams: List[str] = field(default_factory=list)
    received_telegrams: List[str] = field(default_factory=list)
```

Reuse existing models:
- `ConsonModuleConfig` - Individual device
- `ConsonModuleListConfig` - Root container
- `ModuleType.from_code()` - Type conversion

## Service Architecture

Following `ConbusDiscoverService` pattern with `ConbusEventProtocol` and psygnal signals:

```
ConbusExportService
├─ Dependencies (injected via constructor)
│  └─ conbus_protocol: ConbusEventProtocol
├─ Signals (psygnal)
│  ├─ on_progress: Signal(str, int, int)  # device serial, current, total
│  ├─ on_finish: Signal(ConbusExportResponse)
│  └─ on_device_exported: Signal(ConsonModuleConfig)
├─ Protocol Signal Handlers (connected in __init__)
│  ├─ connection_made() → start discovery
│  ├─ telegram_sent(telegram: str)
│  ├─ telegram_received(event: TelegramReceivedEvent) → handle responses
│  ├─ timeout() → finalize export
│  └─ failed(message: str) → emit error
├─ Internal Methods
│  ├─ _handle_discovery_response(serial_number: str)
│  ├─ _handle_datapoint_response(serial_number: str, datapoint: str, value: str)
│  ├─ _query_next_datapoint(serial_number: str)
│  ├─ _query_next_device()
│  ├─ _finalize_export()
│  └─ _write_export_file(path: str)
├─ Context Manager
│  ├─ __enter__() → reset state
│  └─ __exit__() → disconnect signals, stop reactor
└─ Reactor Control
   ├─ set_timeout(seconds: float)
   ├─ set_event_loop(loop: AbstractEventLoop)
   ├─ start_reactor()
   └─ stop_reactor()
```

## Datapoint Mapping

| Field | Datapoint Type | Notes |
|-------|---------------|-------|
| `serial_number` | From discovery | Already available |
| `module_type` | `MODULE_TYPE` | Converted using `ModuleType.from_code()` |
| `module_type_code` | `MODULE_TYPE` | Raw code value |
| `link_number` | `LINK_NUMBER` | Integer 0-99 |
| `module_number` | `MODULE_NUMBER` | Integer (position in system) |
| `sw_version` | `SOFTWARE_VERSION` | String (e.g., "XP130_V0.10.04") |
| `hw_version` | `HARDWARE_VERSION` | String (e.g., "XP130_HW_Rev B") |
| `auto_report_status` | `AUTO_REPORT` | String ("AA", "PP", etc.) |
| `action_table` | N/A | Empty dict (future enhancement) |

## Error Handling

- **No devices found**: Report error, exit with code 1
- **Query timeout**: Log warning, set field to default/empty
- **Invalid response**: Log warning, skip device or use defaults
- **File write error**: Report error, exit with code 1
- **Connection failure**: Report error, exit with code 1

## Progress Reporting

Display progress during export:
```
Discovering devices... (timeout: 5s)
Found 3 devices

Querying device 1/3: 0020041013...
  ✓ Module type: XP130 (13)
  ✓ Link number: 12
  ✓ Software version: XP130_V0.10.04

Querying device 2/3: 1234567890...
  ✓ Module type: XP24 (7)
  ✓ Link number: 9
  ✓ Software version: XP24_V0.34.03

Querying device 3/3: 9876543210...
  ✓ Module type: XP33 (11)
  ✓ Link number: 15
  ✓ Software version: XP33_V1.02.01

Export complete: export.yml (3 devices)
```

## Testing Strategy

### Unit Tests

- Test `_discover_devices()` with mocked discovery service
- Test `_query_device_config()` with mocked datapoint service
- Test `_write_export()` with temp file
- Test error handling (timeout, invalid data)
- Test progress callback invocation

### Integration Tests

- Test full export with XP server emulators
- Verify generated YAML matches schema
- Test round-trip: export → load → validate
- Test multi-device scenarios

## Validation

After export, validate output:
```bash
# Validate exported file can be loaded
xp conbus export
python -c "from xp.models.homekit import ConsonModuleListConfig; \
           ConsonModuleListConfig.from_yaml('export.yml')"
```

## Future Enhancements

1. **Action Table Export**: Query and export device action tables

## Related Components

### Protocol & Communication

- `ConbusEventProtocol` - Async event-driven Conbus communication (injected)
- `TelegramReceivedEvent` - Protocol event model
- `psygnal.Signal` - Event signaling system

### Pattern Template

- `ConbusDiscoverService` - Reference implementation for:
  - `ConbusEventProtocol` integration
  - Signal-based event handling
  - Context manager pattern
  - Reactor control methods
  - Discovery → query flow

### Existing Models (Reuse)

- `ConsonModuleConfig` - Device configuration (Pydantic)
- `ConsonModuleListConfig` - Configuration list (Pydantic)
- `ConbusExportResponse` - Export result (new Pydantic model)
- `ModuleType` - Module type enum and utilities
- `ModuleTypeCode` - Code registry and conversion
- `DataPointType` - Datapoint type definitions
- `SystemFunction` - System function codes
- `TelegramType` - Telegram type enum

### CLI Integration

- Add command to `cli/commands/conbus/conbus.py` group
- Follow `ConbusDiscoverService` CLI command pattern
- Use `@service_command` decorator for DI
- Event loop and reactor setup from CLI utilities
- Progress display via signal handlers
- Error handling via `CLIErrorHandler`

## Dependencies

- **No new dependencies required**
- Reuse existing Pydantic models
- Reuse existing services
- Use standard library YAML serialization

## References

### Project Standards
- `doc/Quality.md` - Quality standards and testing requirements
- `doc/Coding.md` - Type safety, documentation, naming conventions
- `doc/Architecture.md` - Service layer, DI patterns, CLI structure

### Implementation Template
- `src/xp/services/conbus/conbus_discover_service.py` - **Primary pattern reference**
  - ConbusEventProtocol integration
  - psygnal Signal usage
  - Context manager pattern
  - Reactor control
  - Event-driven query flow

### Supporting Components
- `src/xp/models/homekit/homekit_conson_config.py` - Pydantic data models
- `src/xp/services/protocol/conbus_event_protocol.py` - Event protocol
- `src/xp/models/protocol/conbus_protocol.py` - Protocol events
- `src/xp/models/telegram/datapoint_type.py` - Datapoint definitions
- `src/xp/models/telegram/system_function.py` - System functions
