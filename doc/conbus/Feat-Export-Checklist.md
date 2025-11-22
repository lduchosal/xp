# Conbus Export Implementation Checklist

Reference: `doc/conbus/Feat-Export.md`

## Prerequisites
- [ ] Read `doc/Quality.md` - Quality standards and checks
- [ ] Read `doc/Coding.md` - Type safety, documentation, naming conventions
- [ ] Read `doc/Architecture.md` - Layer architecture, DI patterns, signal-based communication
- [ ] Study `src/xp/services/conbus/conbus_discover_service.py` - Primary pattern template

## Model Layer

### ConbusExportResponse Model
- [ ] Create Pydantic dataclass in `src/xp/models/conbus/`
- [ ] Fields: success, config, device_count, output_file, export_status, error, sent_telegrams, received_telegrams
- [ ] Default output_file: "export.yml"
- [ ] Default export_status: "OK"
- [ ] Type hints: Optional[ConsonModuleListConfig], List[str]

## Service Layer - ConbusExportService

### Initialization
- [ ] Constructor injects `ConbusEventProtocol` only
- [ ] Connect protocol signals in `__init__`: connection_made, telegram_sent, telegram_received, timeout, failed
- [ ] Initialize state: discovered_devices, device_configs, device_datapoints_received, export_result, export_status
- [ ] Setup logger: `self.logger = logging.getLogger(__name__)`
- [ ] Define datapoint sequence constant (7 datapoints: MODULE_TYPE, MODULE_TYPE_CODE, LINK_NUMBER, MODULE_NUMBER, SOFTWARE_VERSION, HARDWARE_VERSION, AUTO_REPORT)

### Protocol Signal Handlers
- [ ] `connection_made()` - Send DISCOVERY telegram (serial "0000000000", function F01D)
- [ ] `telegram_sent(telegram: str)` - Record in sent_telegrams list
- [ ] `telegram_received(event: TelegramReceivedEvent)` - Route to discovery or datapoint handlers
- [ ] `timeout()` - Call _finalize_export(), set export_status="FAILED_TIMEOUT" if incomplete
- [ ] `failed(message: str)` - Set export_status="FAILED_CONNECTION", emit on_finish

### Discovery Response Handler
- [ ] `_handle_discovery_response(serial_number: str)` - Add to discovered_devices
- [ ] Initialize device_configs dict for this serial
- [ ] Initialize device_datapoints_received set for this serial
- [ ] Send ALL 7 datapoint queries immediately (protocol handles throttling)
- [ ] Use SystemFunction.READ_DATAPOINT for each query

### Datapoint Response Handler
- [ ] `_handle_datapoint_response(serial_number: str, datapoint: str, value: str)` - Store value in device_configs
- [ ] Add datapoint to device_datapoints_received set
- [ ] Call _check_device_complete() after storing

### Completion Check
- [ ] `_check_device_complete(serial_number: str)` - Check if 7 datapoints received
- [ ] If complete: build ConsonModuleConfig, emit on_device_exported
- [ ] If all devices complete: call _finalize_export()

### Export Finalization
- [ ] `_finalize_export()` - Build ConsonModuleListConfig from device_configs (including partial)
- [ ] Omit fields not received (partial devices)
- [ ] Omit action_table if empty
- [ ] Set export_status based on completion (OK vs FAILED_TIMEOUT)
- [ ] Call _write_export_file()
- [ ] Emit on_finish with ConbusExportResponse

### File Writing
- [ ] `_write_export_file(path: str)` - Serialize ConsonModuleListConfig to YAML
- [ ] Write to "export.yml" in current directory
- [ ] Handle file write errors, set export_status="FAILED_WRITE"

### Signals (psygnal)
- [ ] `on_progress: Signal(str, int, int)` - Emit on each device discovered with serial, current, total
- [ ] `on_finish: Signal(ConbusExportResponse)` - Emit on completion or error
- [ ] `on_device_exported: Signal(ConsonModuleConfig)` - Emit when device has all 7 datapoints

### Context Manager
- [ ] `__enter__()` - Reset state for reuse (clear discovered_devices, device_configs, etc.)
- [ ] `__exit__()` - Disconnect all protocol signals, stop reactor, clear state

### Reactor Control
- [ ] `set_timeout(seconds: float)` - Delegate to conbus_protocol
- [ ] `set_event_loop(loop: AbstractEventLoop)` - Delegate to conbus_protocol
- [ ] `start_reactor()` - Delegate to conbus_protocol
- [ ] `stop_reactor()` - Delegate to conbus_protocol

## CLI Layer

### Command Implementation
- [ ] Create `conbus_export_commands.py` in `cli/commands/conbus/`
- [ ] Add command to `cli/commands/conbus/conbus.py` group
- [ ] Use `@service_command` decorator for DI
- [ ] Follow ConbusDiscoverService CLI pattern exactly

### Command Function
- [ ] Create context manager: `with ConbusExportService(conbus_protocol) as service:`
- [ ] Connect signal handlers: on_progress, on_device_exported, on_finish
- [ ] Set timeout (default 5 seconds)
- [ ] Set event loop from CLI utilities
- [ ] Start reactor
- [ ] Display progress using signal handlers

### Progress Display
- [ ] on_progress handler: Display "Querying device X/Y: serial..."
- [ ] on_device_exported handler: Display "✓ Module type: XP130 (13)" etc
- [ ] on_finish handler: Display "Export complete: export.yml (N devices)" or error

### Error Handling
- [ ] Check export_status in on_finish handler
- [ ] Use CLIErrorHandler for standard error formatting
- [ ] Exit code 1 on FAILED_* statuses
- [ ] Exit code 0 on OK status

## Type Safety
- [ ] All methods have complete type hints
- [ ] Use Optional[T] for nullable types
- [ ] Import types: List, Dict, Set, Optional, Any from typing
- [ ] Import AbstractEventLoop from asyncio
- [ ] Pass `pdm typecheck`

## Documentation
- [ ] Module docstring in ConbusExportService
- [ ] Class docstring with Attributes section
- [ ] Method docstrings with Args/Returns
- [ ] Inline comments for complex logic (datapoint sequence, partial export)
- [ ] CLI command docstring with usage examples

## Testing - Unit Tests

### Service Tests
- [ ] Test `__init__` connects protocol signals
- [ ] Test `_handle_discovery_response` adds device and sends 7 queries
- [ ] Test `_handle_datapoint_response` stores values correctly
- [ ] Test `_check_device_complete` detects 7/7 datapoints
- [ ] Test `_finalize_export` builds ConsonModuleListConfig
- [ ] Test `_write_export_file` serializes YAML
- [ ] Test partial export on timeout (incomplete devices included)
- [ ] Test export_status values: OK, FAILED_TIMEOUT, FAILED_NO_DEVICES, FAILED_WRITE, FAILED_CONNECTION
- [ ] Test signal emission (on_progress, on_device_exported, on_finish)
- [ ] Mock ConbusEventProtocol and verify telegram sending
- [ ] Test context manager __enter__ resets state
- [ ] Test context manager __exit__ disconnects signals
- [ ] Minimum 75% coverage maintained

### Model Tests
- [ ] Test ConbusExportResponse Pydantic validation
- [ ] Test default values (output_file, export_status)
- [ ] Test serialization/deserialization

## Testing - Integration Tests

### Full Export Flow
- [ ] Test with XP24ServerService emulator
- [ ] Test with XP130ServerService emulator
- [ ] Test with multiple device types (XP24, XP130, XP33)
- [ ] Verify generated YAML matches ConsonModuleListConfig schema
- [ ] Test round-trip: export → load → validate
- [ ] Test timeout with partial devices
- [ ] Test no devices found scenario

## Quality Checks
- [ ] `pdm lint` - Ruff linting passes
- [ ] `pdm format` - Black formatting applied
- [ ] `pdm typecheck` - Mypy strict mode passes
- [ ] `pdm absolufy` - Absolute imports
- [ ] `pdm test-quick` - Fast tests pass
- [ ] `pdm check` - All quality checks pass

## Architecture Compliance

### Dependency Injection
- [ ] ConbusEventProtocol injected via constructor
- [ ] No direct service instantiation in service layer
- [ ] Use `self.logger = logging.getLogger(__name__)`

### Signal-Based Communication
- [ ] Use psygnal.Signal for all events
- [ ] Connect to protocol signals in __init__
- [ ] Disconnect signals in __exit__
- [ ] No direct protocol method calls except send_telegram

### Layer Separation
- [ ] Service layer has no CLI concerns
- [ ] Service emits signals, CLI displays output
- [ ] Protocol events transformed to service-level signals

## Error Handling
- [ ] No devices found: export_status="FAILED_NO_DEVICES", exit code 1
- [ ] Timeout: partial export with export_status="FAILED_TIMEOUT"
- [ ] Missing datapoints: omit fields in partial device
- [ ] Invalid response: log warning, continue processing
- [ ] File write error: export_status="FAILED_WRITE", exit code 1
- [ ] Connection failure: export_status="FAILED_CONNECTION", exit code 1

## Logging
- [ ] DEBUG: Connection established, discovery sent
- [ ] DEBUG: Device discovered with serial
- [ ] DEBUG: Datapoint received for device
- [ ] DEBUG: Device complete (7/7 datapoints)
- [ ] INFO: Export finalized, file written
- [ ] WARNING: Partial export, missing datapoints
- [ ] ERROR: File write errors, connection failures
- [ ] No sensitive data in logs

## Edge Cases Validated
- [ ] No devices on network
- [ ] Single device with all datapoints
- [ ] Multiple devices with mixed completion states
- [ ] Timeout before any datapoints received
- [ ] Timeout after some datapoints received
- [ ] Duplicate discovery responses (idempotent)
- [ ] Out-of-order datapoint responses
- [ ] Invalid datapoint values (log and continue)

## Pre-Commit
- [ ] Run `pdm check` - all quality checks pass
- [ ] Review git diff for unintended changes
- [ ] Verify export.yml can be loaded by ConsonModuleListConfig.from_yaml()
- [ ] Commit message follows convention
