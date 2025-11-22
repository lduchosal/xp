# Migration: ConbusProtocol to ConbusEventProtocol

## TL;DR
Migrate 12 services from inheritance-based `ConbusProtocol` to composition-based `ConbusEventProtocol`. **Key changes**: Constructor takes protocol parameter, connect signals in `__init__` and disconnect in `__exit__`, delegate reactor lifecycle to protocol, use context manager in CLI.

**Estimated Time**: 2-3 hours per service
**Order**: Follow checklist sequentially (1�10)

## � CRITICAL: Read This First

### Breaking Changes
1. **Callbacks → Signals**: Replace callback parameters with Signal attributes (e.g., `finish_callback` → `on_finish: Signal`)
2. **CLI Update Required**: Commands connect to service signals instead of passing callbacks
3. **Context Manager**: Services MUST implement `__enter__`/`__exit__` (no longer inherited)
4. **Method Signature**: `timeout()` changes from `-> bool` to `-> None`
5. **Constructor**: Takes `ConbusEventProtocol` instead of `ConbusClientConfig` + `reactor`
6. **Lifecycle Methods**: Must add `set_timeout()`, `start_reactor()`, `stop_reactor()`

### Common Mistakes to Avoid
- L DON'T call `stop_reactor()` in `timeout()` - protocol handles it automatically
- L DON'T call `start_reactor()` in service methods - caller's responsibility
- L DON'T use `bytes` for `telegram_sent` parameter - signal emits `str`
- L DON'T forget to disconnect signals in `__exit__` - causes memory leaks
- L DON'T use `self._conbus_protocol` - it's `self.conbus_protocol` (no underscore)
-  DO set timeout on protocol: `self.conbus_protocol.timeout_seconds = timeout_seconds`
-  DO reset state in `__enter__` for singleton reuse
-  DO maintain singleton scope in container registration
-  DO call `self.stop_reactor()` in `__exit__`

## Scope

### Services to Migrate
1. [x] done: `ConbusBlinkService` (src/xp/services/conbus/conbus_blink_service.py:22)
2. `ConbusRawService` (src/xp/services/conbus/conbus_raw_service.py:18)
3. `ConbusCustomService` (src/xp/services/conbus/conbus_custom_service.py:22)
4. `ConbusScanService` (src/xp/services/conbus/conbus_scan_service.py:21)
5. `ConbusDatapointService` (src/xp/services/conbus/conbus_datapoint_service.py:22)
6. `ConbusDatapointQueryAllService` (src/xp/services/conbus/conbus_datapoint_queryall_service.py:22)
7. `WriteConfigService` (src/xp/services/conbus/write_config_service.py:22)
8. `ConbusOutputService` (src/xp/services/conbus/conbus_output_service.py:33)
9. `ConbusBlinkAllService` (src/xp/services/conbus/conbus_blink_all_service.py:22)
10. `ActionTableService` (src/xp/services/conbus/actiontable/actiontable_download_service.py:19)
11. `ActionTableUploadService` (src/xp/services/conbus/actiontable/actiontable_upload_service.py:18)
12. `MsActionTableService` (src/xp/services/conbus/actiontable/msactiontable_service.py:34)

### Reference Implementation
- **ConbusDiscoverService** (src/xp/services/conbus/conbus_discover_service.py:23) - Primary pattern
- **ConbusReceiveService** (src/xp/services/conbus/conbus_receive_service.py:18) - Already migrated

## Architecture Changes

### Old Pattern (Inheritance)
```python
class MsActionTableService(ConbusProtocol):
    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
        telegram_service: TelegramService,
    ):
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service

    def connection_established(self) -> None:
        self.send_telegram(...)

    def timeout(self) -> bool:
        self.failed("Timeout")
        return False  # Stop reactor
```

**Problems**:
- Tight coupling to protocol lifecycle
- Cannot reuse protocol across services
- Hard to test (requires full reactor stack)
- Services manage reactor lifecycle

### New Pattern (Composition + Signals)
```python
class MsActionTableService:
    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_service: TelegramService,
    ):
        self.conbus_protocol = conbus_protocol
        self.telegram_service = telegram_service

        # Connect signals in __init__
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:  # Renamed from connection_established
        self.conbus_protocol.send_telegram(...)

    def timeout(self) -> None:  # No return value
        self.failed("Timeout")
        # Protocol handles reactor stop automatically

    def set_timeout(self, timeout_seconds: float) -> None:
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def start_reactor(self) -> None:
        self.conbus_protocol.start_reactor()

    def stop_reactor(self) -> None:
        self.conbus_protocol.stop_reactor()

    def __enter__(self) -> "MsActionTableService":
        # Reset state for singleton reuse
        self.response = ServiceResponse(success=False)
        self.msactiontable_data = []
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        # Disconnect all signals
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        # Disconnect service signals if any
        # self.on_progress.disconnect()
        self.stop_reactor()
```

**Benefits**:
- Loose coupling via dependency injection
- Protocol reusable across services
- Easy to test (mock protocol interface)
- Protocol manages its own lifecycle

## Callbacks → Signals Migration

### Old Pattern (Callbacks)
```python
class ConbusBlinkService(ConbusProtocol):
    def __init__(self, ...):
        super().__init__(...)
        self.finish_callback: Optional[Callable[[ConbusBlinkResponse], None]] = None
        self.progress_callback: Optional[Callable[[str], None]] = None

    def send_blink_telegram(
        self,
        finish_callback: Callable[[ConbusBlinkResponse], None],
        progress_callback: Callable[[str], None],
    ) -> None:
        self.finish_callback = finish_callback
        self.progress_callback = progress_callback
        self.start_reactor()

    def telegram_received(self, event: TelegramReceivedEvent) -> None:
        if self.progress_callback:
            self.progress_callback("Processing...")
        # ... processing ...
        if self.finish_callback:
            self.finish_callback(self.response)

# CLI usage
def on_finish(response: ConbusBlinkResponse) -> None:
    click.echo(json.dumps(response.to_dict()))

service.send_blink_telegram(on_finish, None)
```

**Problems**:
- Callbacks stored as mutable state
- Must pass callbacks through multiple method calls
- Hard to connect multiple listeners
- No automatic cleanup

### New Pattern (Signals)
```python
from psygnal import Signal

class ConbusBlinkService:
    # Define signals as class attributes
    on_finish: Signal = Signal(ConbusBlinkResponse)
    on_progress: Signal = Signal(str)

    def __init__(self, conbus_protocol: ConbusEventProtocol):
        self.conbus_protocol = conbus_protocol
        # Signals are already initialized by class definition

    def send_blink_telegram(self) -> None:
        # No callback parameters needed
        pass

    def telegram_received(self, event: TelegramReceivedEvent) -> None:
        self.on_progress.emit("Processing...")
        # ... processing ...
        self.on_finish.emit(self.response)

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        # Disconnect all signals
        self.on_finish.disconnect()
        self.on_progress.disconnect()
        self.stop_reactor()

# CLI usage
def on_finish(response: ConbusBlinkResponse) -> None:
    click.echo(json.dumps(response.to_dict()))
    service.stop_reactor()  # CRITICAL: Stop reactor when done

with service:
    service.on_finish.connect(on_finish)  # Connect in CLI
    service.start_reactor()
```

**Benefits**:
- Signals are stateless (no mutable callback storage)
- Multiple listeners can connect to same signal
- Automatic type checking (signal signature)
- Clean separation: service emits, caller connects
- CLI controls when to connect/disconnect

### Migration Steps for Callbacks → Signals

1. **Identify Callbacks**: Find all `*_callback` attributes and parameters
2. **Define Signals**: Add class-level signal definitions with correct types
3. **Remove Callback Storage**: Delete `self.*_callback = None` from `__init__`
4. **Remove Callback Parameters**: Delete callback params from `send_*()` methods
5. **Replace Callback Calls**: Change `if self.callback: self.callback(data)` to `self.signal.emit(data)`
6. **Add Signal Disconnection**: Add `self.signal.disconnect()` to `__exit__`
7. **Update CLI**: Connect to signals inside `with service:` block
8. **Update Tests**: Mock signals or connect test handlers

## Migration Checklist

### 1. Class Definition [CRITICAL - DO FIRST]
- [ ] Remove inheritance: `class Service(ConbusProtocol)` � `class Service`
- [ ] Keep service-specific state (callbacks, response models, etc.)

### 2. Constructor Refactoring [CRITICAL]
- [ ] Replace `cli_config: ConbusClientConfig, reactor: PosixReactorBase` with `conbus_protocol: ConbusEventProtocol`
- [ ] Remove `super().__init__(cli_config, reactor)` call
- [ ] Store protocol: `self.conbus_protocol = conbus_protocol`
- [ ] Keep other dependencies (telegram_service, serializers, etc.)
- [ ] Initialize response models and state
- [ ] Connect signals after storing protocol (next step)

### 3. Signal Connections [CRITICAL]
Connect event handlers in `__init__` after storing protocol reference:
- [ ] `self.conbus_protocol.on_connection_made.connect(self.connection_made)`
- [ ] `self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)`
- [ ] `self.conbus_protocol.on_telegram_received.connect(self.telegram_received)`
- [ ] `self.conbus_protocol.on_timeout.connect(self.timeout)`
- [ ] `self.conbus_protocol.on_failed.connect(self.failed)`
- [ ] Note: Only connect signals the service actually uses (not all services use all 5)

### 4. Method Updates [IMPORTANT]
- [ ] Rename: `connection_established()` � `connection_made()`
- [ ] `telegram_sent(telegram_sent: str)` - Parameter is `str`, not `bytes`
- [ ] `telegram_received(telegram_received: TelegramReceivedEvent)` - No changes needed
- [ ] `timeout()` - Change return type from `-> bool` to `-> None`
- [ ] `timeout()` - Remove `return False` statement
- [ ] `timeout()` - Remove any `self._stop_reactor()` calls
- [ ] `failed(message: str)` - Remove `self._stop_reactor()` calls
- [ ] Replace `self.send_telegram()` with `self.conbus_protocol.send_telegram()`
- [ ] Replace `self.timeout_seconds` with `self.conbus_protocol.timeout_seconds`

### 5. Lifecycle Delegation Methods [CRITICAL]
Add these delegation methods to all services:
- [ ] Add `set_timeout(timeout_seconds: float)`:
  ```python
  def set_timeout(self, timeout_seconds: float) -> None:
      """Set operation timeout."""
      self.conbus_protocol.timeout_seconds = timeout_seconds
  ```
- [ ] Add `start_reactor()`:
  ```python
  def start_reactor(self) -> None:
      """Start the reactor."""
      self.conbus_protocol.start_reactor()
  ```
- [ ] Add `stop_reactor()`:
  ```python
  def stop_reactor(self) -> None:
      """Stop the reactor."""
      self.conbus_protocol.stop_reactor()
  ```
- [ ] Optional: Add `set_event_loop(event_loop)` - only if service needs async integration
- [ ] Update existing `start()` or `send_*()` methods - remove internal `self.start_reactor()` calls

### 6. Context Manager [CRITICAL - BLOCKS CLI]
- [ ] Add `__enter__(self) -> "ServiceName"` returning `self`
- [ ] Reset state in `__enter__` for singleton reuse:
  - Response/result models: Create new instance (e.g., `self.response = ServiceResponse(success=False)`)
  - Accumulated lists/dicts: Clear or reinitialize to empty (`[]`, `{}`)
  - Operation-specific state: Reset to defaults (serial_number, counters, etc.)
  - Callbacks: Keep if set via constructor, clear if set via start() methods
- [ ] Add `__exit__(self, _exc_type, _exc_val, _exc_tb) -> None`
- [ ] Disconnect protocol signals in `__exit__`:
  ```python
  self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
  self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
  self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
  self.conbus_protocol.on_timeout.disconnect(self.timeout)
  self.conbus_protocol.on_failed.disconnect(self.failed)
  ```
- [ ] Disconnect service-specific signals (if any): `self.on_progress.disconnect()`, etc.
- [ ] **CRITICAL**: Call `self.stop_reactor()` at end of `__exit__`

### 7. Dependencies Registration [CRITICAL - BLOCKS CLI]
Update dependency injection in `src/xp/utils/dependencies.py`:
- [ ] Update factory lambda for the service
- [ ] Before: `Service(cli_config=..., reactor=...)`
- [ ] After: `Service(conbus_protocol=self.container.resolve(ConbusEventProtocol), ...)`
- [ ] Keep singleton scope: `scope=punq.Scope.singleton`
- [ ] Keep other dependencies unchanged (telegram_service, serializers, etc.)
- [ ] Note: Keep old `ConbusProtocol` registration during migration (other services may use it)
- [ ] Final step (after all 12 services): Remove `ConbusProtocol` registration

### 8. CLI Commands [CRITICAL - BLOCKS CLI]
Update CLI command for the service:
- [ ] **Mandatory**: Use `with service:` context manager (ensures signal cleanup)
- [ ] **CRITICAL**: Add `service.stop_reactor()` call in signal handlers (especially `on_finish`)
- [ ] Pattern:
  ```python
  def on_finish(response: ServiceResponse) -> None:
      click.echo(json.dumps(response.to_dict()))
      service.stop_reactor()  # CRITICAL: Stop reactor when done

  with service:
      # Connect service-specific signals (if any)
      service.on_finish.connect(on_finish)
      service.on_progress.connect(progress)
      # Setup
      service.set_timeout(5)
      # Start (blocks until completion)
      service.start_reactor()
  # Automatic cleanup via __exit__
  ```
- [ ] Verify context manager usage still works
- [ ] Verify command interface remains unchanged for users

### 9. Unit Testing [IMPORTANT - PREVENTS REGRESSION]
Create or update `tests/unit/test_services/test_<service>_service.py`:
- [ ] Create fixture for mock `ConbusEventProtocol`
- [ ] Test signal connections established in `__init__`
- [ ] Test `connection_made()` behavior
- [ ] Test `telegram_sent()` parameter type (str, not bytes)
- [ ] Test `telegram_received()` updates response and calls callbacks
- [ ] Test `timeout()` return type is None
- [ ] Test `failed()` sets error message
- [ ] Test `set_timeout()` delegates to protocol
- [ ] Test `start_reactor()` delegates to protocol
- [ ] Test `stop_reactor()` delegates to protocol
- [ ] Test `__enter__` resets state
- [ ] Test `__exit__` disconnects all signals and stops reactor

### 10. Quality Validation [IMPORTANT]
Run all quality checks:
- [ ] `pdm typecheck` - Verify all type hints correct
- [ ] `pdm lint` - Ensure code style compliance
- [ ] `pdm format` - Apply formatting
- [ ] `pdm test-quick` - Validate unit tests pass
- [ ] `pdm check` - Full quality validation suite
- [ ] Manual CLI test: `xp conbus <command> <args>`
- [ ] Verify 75% minimum test coverage maintained

## Service-Specific Notes

### ConbusBlinkService (Priority 1)
**Signals used**: connection_made, telegram_received, timeout, failed (4/5)
**Service signals**: None
**State reset in `__enter__`**:
- `self.service_response = ConbusBlinkResponse(success=False, ...)`
- `self.serial_number = ""`
- `self.on_or_off = "none"`

### ConbusRawService (Priority 2)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.raw_response = ConbusRawResponse(success=False)`
- Clear received telegrams list

### ConbusCustomService (Priority 3)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.custom_response = ConbusCustomResponse(success=False)`

### ConbusScanService (Priority 4)
**Signals used**: All 5
**Service signals**: on_progress, on_finish
**State reset in `__enter__`**:
- `self.scan_result = ConbusScanResponse(success=False)`
- `self.discovered_devices = []`

### ConbusDatapointService (Priority 5)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.datapoint_response = ConbusDatapointResponse(success=False)`

### ConbusDatapointQueryAllService (Priority 6)
**Signals used**: All 5
**Service signals**: on_progress
**State reset in `__enter__`**:
- `self.query_all_response = ConbusDatapointQueryAllResponse(success=False)`
- `self.datapoints = []`

### WriteConfigService (Priority 7)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.write_config_response = WriteConfigResponse(success=False)`

### ConbusOutputService (Priority 8)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.output_response = ConbusOutputResponse(success=False)`
- `self.output_state = ""`

### ConbusBlinkAllService (Priority 9)
**Signals used**: All 5
**Service signals**: on_progress
**State reset in `__enter__`**:
- `self.blink_all_response = ConbusBlinkAllResponse(success=False)`
- `self.device_results = []`

### ActionTableService (Priority 10)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.action_table_response = ActionTableResponse(success=False)`
- `self.action_table_data = []`

### ActionTableUploadService (Priority 11)
**Signals used**: All 5
**Service signals**: None
**State reset in `__enter__`**:
- `self.upload_response = ActionTableUploadResponse(success=False)`
- `self.upload_buffer = []`

### MsActionTableService (Priority 12 - Most Complex)
**Signals used**: All 5
**Service signals**: None
**Complex serializer dependencies**: xp20, xp24, xp33
**State reset in `__enter__`**:
- `self.msactiontable_data = []`
- `self.serial_number = ""`
- `self.xpmoduletype = ""`
- `self.progress_callback = None`
- `self.error_callback = None`
- `self.finish_callback = None`

## Common Patterns

### Timeout Handling
**Before**:
```python
def timeout(self) -> bool:
    self.failed("Timeout")
    return False  # Stop reactor
```

**After**:
```python
def timeout(self) -> None:
    self.failed("Timeout")
    # Protocol stops reactor automatically
```

### Failed Handling
**Before**:
```python
def failed(self, message: str) -> None:
    if self.error_callback:
        self.error_callback(message)
    self._stop_reactor()
```

**After**:
```python
def failed(self, message: str) -> None:
    if self.error_callback:
        self.error_callback(message)
    # Protocol handles reactor lifecycle
```

### Start Method
**Before**:
```python
def start(self, ..., timeout_seconds: float) -> None:
    if timeout_seconds:
        self.timeout_seconds = timeout_seconds
    self.start_reactor()
```

**After**:
```python
def start(self, ..., timeout_seconds: float) -> None:
    if timeout_seconds:
        self.conbus_protocol.timeout_seconds = timeout_seconds
    # Caller invokes start_reactor()

def set_timeout(self, timeout_seconds: float) -> None:
    self.conbus_protocol.timeout_seconds = timeout_seconds

def start_reactor(self) -> None:
    self.conbus_protocol.start_reactor()
```

### Context Manager Pattern
```python
def __enter__(self) -> "ServiceName":
    """Enter context manager - reset state for singleton reuse."""
    # Reset response models (create new instance)
    self.response = ServiceResponse(success=False)
    # Clear accumulated data
    self.data_buffer = []
    # Reset operation-specific state
    self.serial_number = ""
    return self

def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
    """Exit context manager - cleanup signals and reactor."""
    # Disconnect protocol signals
    self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
    self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
    self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
    self.conbus_protocol.on_timeout.disconnect(self.timeout)
    self.conbus_protocol.on_failed.disconnect(self.failed)
    # Disconnect service signals (if any)
    # self.on_progress.disconnect()
    # self.on_finish.disconnect()
    # Stop reactor
    self.stop_reactor()
```

## Migration Order

Recommended order (simplest to most complex):

1. **ConbusBlinkService** - Simple request/response
2. **ConbusRawService** - Minimal state
3. **ConbusCustomService** - Similar to blink
4. **ConbusScanService** - Discovery-like pattern
5. **ConbusDatapointService** - Datapoint handling
6. **ConbusDatapointQueryAllService** - Multiple datapoints
7. **WriteConfigService** - Config operations
8. **ConbusOutputService** - Output management
9. **ConbusBlinkAllService** - Batch operations
10. **ActionTableService** - File operations
11. **ActionTableUploadService** - Upload logic
12. **MsActionTableService** - Most complex (multiple serializers)

## Important Notes

### Signal Lifecycle
**Pattern**: Connect once in `__init__`, disconnect in `__exit__`, never reconnect

Based on `ConbusDiscoverService`:
- Signals connected in `__init__` (lines 49-53)
- Signals disconnected in `__exit__` (lines 312-319)
- State reset in `__enter__` without reconnecting signals
- Signals remain connected for service lifetime, only disconnected when context exits

**Rationale**: psygnal signals handle multiple connections efficiently. Reconnecting on each use is unnecessary overhead.

### Timeout Behavior
**Important**: Services cannot dynamically extend timeout after it fires

Old behavior (`ConbusProtocol`):
```python
def timeout(self) -> bool:
    return True  # Continue waiting, reset timeout
```

New behavior (`ConbusEventProtocol`):
```python
def timeout(self) -> None:
    # No return value - protocol automatically stops
    # Cannot continue waiting
```

**Impact**: Services must set correct timeout upfront via `set_timeout()`. No dynamic extension supported.

### Error Handling

**Type Safety**
- DI container guarantees non-None dependencies
- Type checker validates all parameters
- No defensive None checks needed in constructors

**Signal Validation**
- psygnal validates handler signatures at `.connect()` time
- TypeError raised immediately if signature mismatch
- Fail fast during initialization

## Troubleshooting

### Reactor doesn't stop after timeout
**Symptom**: Service hangs, never calls finish_callback
**Cause**: Signal not connected properly
**Fix**: Verify `self.conbus_protocol.on_timeout.connect(self.timeout)` in `__init__`
**Debug**: Add logging in `timeout()` to verify it's being called

### TypeError: 'bytes' object has no attribute
**Symptom**: TypeError when telegram_sent signal emits
**Cause**: Method signature mismatch - expecting bytes instead of str
**Fix**: Verify `telegram_sent` parameter type is `str`, not `bytes`
**Note**: Signal emits `str`, not `bytes`

### Service state persists between calls
**Symptom**: Previous data appears in new requests
**Cause**: Singleton scope with mutable state not being reset
**Fix**: Reset all mutable state in `__enter__` method
**Pattern**: `self.response = ServiceResponse(success=False)`

### Memory leak in long-running process
**Symptom**: Memory grows over time with repeated calls
**Cause**: Signals not disconnected in `__exit__`
**Fix**: Add disconnect calls in `__exit__` for all signals
**Verify**: Monitor memory with repeated CLI calls

### Reactor doesn't stop on exit
**Symptom**: Program hangs after context manager exits
**Cause**: Missing `self.stop_reactor()` call in `__exit__`
**Fix**: Add `self.stop_reactor()` as last line of `__exit__`

### Import errors after refactoring
**Symptom**: ModuleNotFoundError or ImportError
**Cause**: Missing import for ConbusEventProtocol
**Fix**: Add `from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol`
**Check**: Remove old imports of ConbusProtocol if unused

### Container resolution fails
**Symptom**: "Cannot resolve Service" error
**Cause**: Factory lambda not updated in dependencies.py
**Fix**: Verify registration uses new constructor signature
**Debug**: Check ConbusEventProtocol is registered before service

### TypeError: disconnect() called with wrong signature
**Symptom**: Error when disconnecting signals in `__exit__`
**Cause**: Using `self._conbus_protocol` instead of `self.conbus_protocol`
**Fix**: Verify attribute name is `self.conbus_protocol` (no underscore)

### Common Issues Summary
| Issue | Cause | Fix |
|-------|-------|-----|
| Cannot resolve Service | Missing registration in dependencies.py | Add service registration before use |
| Signal connection TypeError | Handler signature mismatch | Check signal definition in ConbusEventProtocol |
| Memory leak | Signals not disconnected | Verify `__exit__` calls all `.disconnect()` |
| State persists between calls | State not reset in `__enter__` | Reset all mutable state |
| Reactor hangs on exit | Missing `stop_reactor()` in `__exit__` | Add `self.stop_reactor()` call |
| Typo: `_conbus_protocol` | Wrong attribute name | Use `self.conbus_protocol` (no underscore) |

## Validation

### Per Service
```bash
# After each service migration
pdm typecheck
pdm lint
pdm format
pdm test-quick

# Test CLI command
xp conbus <command> <args>
```

### Final Validation
```bash
# All quality checks
pdm check

# Full test suite
pdm test

# Integration tests
xp conbus blink 0012345678 on
xp conbus scan
xp conbus datapoint read 0012345678 00
```

## Completion Criteria

### Must Pass (Per Service)
- [ ] All quality checks pass (`pdm check`)
- [ ] CLI command works identically to before
- [ ] No breaking changes to public API or command interface
- [ ] All unit tests pass with 75%+ coverage
- [ ] Integration tests show no regression

### Final Completion (All Services)
- [ ] All 12 services migrated
- [ ] All quality checks pass (`pdm check`)
- [ ] All tests pass (`pdm test`)
- [ ] No breaking changes to CLI commands
- [ ] All services use ConbusEventProtocol
- [ ] No services inherit from ConbusProtocol
- [ ] Signal connections/disconnections verified
- [ ] Context managers tested
- [ ] ConbusProtocol registration removed from dependencies.py

## Key Differences Summary

### Lifecycle Management
- **Old**: Service controls lifecycle via override methods, returns bool to stop reactor
- **New**: Protocol emits signals, service handles events, protocol manages reactor lifecycle

### Coupling
- **Old**: Inheritance creates tight coupling to protocol internals
- **New**: Composition allows dependency injection and mocking

### Testability
- **Old**: Must instantiate full protocol stack (reactor, config) for testing
- **New**: Mock protocol interface, test service in isolation

### Reusability
- **Old**: Cannot reuse protocol with multiple services simultaneously
- **New**: Single protocol instance can notify multiple subscribers

### Reactor Control
- **Old**: Service calls `self.start_reactor()` and returns False to stop
- **New**: Caller calls `service.start_reactor()`, protocol stops automatically on timeout

## References
- **Architecture**: doc/Architecture.md - Dependency injection patterns
- **Coding**: doc/Coding.md - Type safety, error handling, service patterns
- **Quality**: doc/Quality.md - Validation commands and coverage requirements
- **Reference**: src/xp/services/conbus/conbus_discover_service.py:23 - Complete migration example
- **Reference**: src/xp/services/conbus/conbus_receive_service.py:18 - Already migrated
- **Protocol**: src/xp/services/protocol/conbus_event_protocol.py - Signal interface

## Callback to Signal Migration - Quick Reference

### Pattern Comparison

**Old (Callbacks)**:
- Constructor: `self.finish_callback: Optional[Callable] = None`
- Method params: `finish_callback: Callable[[Response], None]`
- Store: `self.finish_callback = finish_callback`
- Call: `if self.finish_callback: self.finish_callback(result)`
- CLI: `service.send_telegram(..., finish_callback=on_finish)`

**New (Signals)**:
- Class attr: `on_finish: Signal = Signal(Response)`
- No params needed
- No storage needed
- Emit: `self.on_finish.emit(result)`
- CLI: `service.on_finish.connect(on_finish)` + `service.stop_reactor()` in handler
- Exit: `self.on_finish.disconnect()`

### Services with Callbacks to Migrate

- ConbusBlinkService: finish_callback → on_finish
- ConbusScanService: progress_callback, finish_callback → on_progress, on_finish
- ConbusDatapointQueryAllService: progress_callback → on_progress
- ConbusBlinkAllService: progress_callback, finish_callback → on_progress, on_finish
- MsActionTableService: progress_callback, error_callback, finish_callback → on_progress, on_error, on_finish


## Callback → Signal Migration Checklist (For Services with Callbacks)

If your service has callback parameters (finish_callback, progress_callback, error_callback):

- [ ] Add Signal import: `from psygnal import Signal`
- [ ] Define signals as class attributes before `__init__`:
  ```python
  on_finish: Signal = Signal(ServiceResponse)
  on_progress: Signal = Signal(str)  # if needed
  ```
- [ ] Remove callback attributes from `__init__`: Delete `self.finish_callback = None`
- [ ] Remove callback parameters from methods: Delete `finish_callback: Callable` from method signatures
- [ ] Replace callback calls with signal emissions:
  - Before: `if self.finish_callback: self.finish_callback(result)`
  - After: `self.on_finish.emit(result)`
- [ ] Add signal disconnection to `__exit__`: `self.on_finish.disconnect()`
- [ ] Update CLI commands:
  - Remove callback from method call
  - Add signal connection: `service.on_finish.connect(on_finish)`
  - **CRITICAL**: Add `service.stop_reactor()` in `on_finish` handler to stop reactor when operation completes
- [ ] Update tests to use signal pattern (mock or connect handlers)

