# Migration: ConbusProtocol to ConbusEventProtocol

## TL;DR
Migrate 12 services from inheritance-based `ConbusProtocol` to composition-based `ConbusEventProtocol`. **Key changes**: Constructor takes protocol parameter, connect signals in `__init__` and disconnect in `__exit__`, delegate reactor lifecycle to protocol, use context manager in CLI.

## Scope

### Services to Migrate
- `MsActionTableService` (src/xp/services/conbus/actiontable/msactiontable_service.py:34)
- `ActionTableService` (src/xp/services/conbus/actiontable/actiontable_download_service.py:19)
- `ActionTableUploadService` (src/xp/services/conbus/actiontable/actiontable_upload_service.py:18)
- `ConbusBlinkService` (src/xp/services/conbus/conbus_blink_service.py:22)
- `ConbusBlinkAllService` (src/xp/services/conbus/conbus_blink_all_service.py:22)
- `ConbusCustomService` (src/xp/services/conbus/conbus_custom_service.py:22)
- `ConbusDatapointService` (src/xp/services/conbus/conbus_datapoint_service.py:22)
- `ConbusDatapointQueryAllService` (src/xp/services/conbus/conbus_datapoint_queryall_service.py:22)
- `ConbusOutputService` (src/xp/services/conbus/conbus_output_service.py:33)
- `ConbusRawService` (src/xp/services/conbus/conbus_raw_service.py:18)
- `ConbusScanService` (src/xp/services/conbus/conbus_scan_service.py:21)
- `WriteConfigService` (src/xp/services/conbus/write_config_service.py:22)

### Reference Implementation
- ConbusDiscoverService (src/xp/services/conbus/conbus_discover_service.py:23)
- Migration spec (doc/conbus/Refactor-ConbusEventProtocol-For-ConbusReceiveService.md)

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

**Issues**:
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

        # Connect signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_timeout.connect(self.timeout)

    def connection_made(self) -> None:  # Renamed
        self.conbus_protocol.send_telegram(...)

    def timeout(self) -> None:  # No return value
        self.failed("Timeout")
        # Protocol handles reactor stop
```

**Benefits**:
- Loose coupling via dependency injection
- Protocol reusable across services
- Easy to test (mock protocol interface)
- Protocol manages its own lifecycle

## Migration Checklist

### Per Service

#### 1. Class Definition
- [ ] Remove inheritance: `class Service(ConbusProtocol)` → `class Service`
- [ ] Keep service-specific state (callbacks, response models, etc.)

#### 2. Constructor
- [ ] Replace `cli_config: ConbusClientConfig, reactor: PosixReactorBase` with `conbus_protocol: ConbusEventProtocol`
- [ ] Remove `super().__init__(cli_config, reactor)` call
- [ ] Store protocol: `self.conbus_protocol = conbus_protocol`
- [ ] Keep other dependencies (telegram_service, serializers, etc.)
- [ ] Connect signals after storing protocol

#### 3. Signal Connections (in `__init__`)
- [ ] `on_connection_made.connect(self.connection_made)`
- [ ] `on_telegram_sent.connect(self.telegram_sent)`
- [ ] `on_telegram_received.connect(self.telegram_received)`
- [ ] `on_timeout.connect(self.timeout)`
- [ ] `on_failed.connect(self.failed)`

#### 4. Method Updates
- [ ] Rename: `connection_established()` → `connection_made()`
- [ ] `telegram_sent(str)` - Already correct signature
- [ ] `telegram_received(TelegramReceivedEvent)` - No changes
- [ ] `timeout()` - Change `-> bool` to `-> None`
- [ ] `timeout()` - Remove `return False` statement
- [ ] `timeout()` - Remove `self._stop_reactor()` calls
- [ ] `failed(str)` - Remove `self._stop_reactor()` calls
- [ ] Replace `self.send_telegram()` with `self.conbus_protocol.send_telegram()`
- [ ] Replace `self.timeout_seconds` with `self.conbus_protocol.timeout_seconds`

#### 5. Lifecycle Delegation Methods
- [ ] Add `set_timeout(timeout_seconds: float)` - delegates to `self.conbus_protocol.timeout_seconds = timeout_seconds`
- [ ] Add `start_reactor()` - delegates to `self.conbus_protocol.start_reactor()`
- [ ] Add `stop_reactor()` - delegates to `self.conbus_protocol.stop_reactor()`
- [ ] Optional: Add `set_event_loop(event_loop)` - only if service needs async integration
- [ ] Update existing `start()` or `send_*()` methods - remove internal `self.start_reactor()` calls

#### 6. Context Manager
- [ ] Add `__enter__(self) -> "ServiceName"` returning `self`
- [ ] Reset state in `__enter__` for singleton reuse:
  - Response/result models: Create new instance (e.g., `self.response = ServiceResponse(success=False)`)
  - Accumulated lists/dicts: Clear or reinitialize to empty (`[]`, `{}`)
  - Operation-specific state: Reset to defaults (serial_number, counters, etc.)
  - Callbacks: Keep if set via constructor, clear if set via start() methods
- [ ] Add `__exit__(self, _exc_type, _exc_val, _exc_tb)` disconnecting all signals
- [ ] Disconnect protocol signals:
  ```python
  self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
  self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
  self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
  self.conbus_protocol.on_timeout.disconnect(self.timeout)
  self.conbus_protocol.on_failed.disconnect(self.failed)
  ```
- [ ] Disconnect service-specific signals (if any): `self.on_progress.disconnect()`, etc.
- [ ] Call `self.stop_reactor()` in `__exit__`

#### 7. Dependencies Registration
- [ ] Update factory in `src/xp/utils/dependencies.py`
- [ ] Change constructor parameters
- [ ] Before: `Service(cli_config=..., reactor=...)`
- [ ] After: `Service(conbus_protocol=self.container.resolve(ConbusEventProtocol))`
- [ ] Keep singleton scope: `punq.Scope.singleton`
- [ ] Note: Keep old `ConbusProtocol` registration during migration (other services may still use it)
- [ ] Final step (after all 12 services): Remove `ConbusProtocol` registration from dependencies.py

#### 8. CLI Commands
- [ ] **Mandatory**: Use `with service:` context manager (ensures signal cleanup)
- [ ] Connect service-specific signals inside context (if any)
- [ ] Call setup methods: `service.set_timeout(seconds)`
- [ ] Add explicit `service.start_reactor()` after setup
- [ ] Pattern:
  ```python
  with service:
      # Connect signals (if service provides them)
      service.on_finish.connect(callback)
      # Setup
      service.set_timeout(5)
      # Start (blocks until completion)
      service.start_reactor()
  # Automatic cleanup via __exit__
  ```

#### 9. Tests
- [ ] Create/update unit tests
- [ ] Mock ConbusEventProtocol for testing
- [ ] Test signal connections
- [ ] Test all event handlers
- [ ] Test context manager (state reset, signal disconnection)
- [ ] Update integration tests if needed

#### 10. Validation
- [ ] `pdm typecheck` - Type safety
- [ ] `pdm lint` - Code style
- [ ] `pdm format` - Formatting
- [ ] `pdm test-quick` - Unit tests
- [ ] `pdm check` - Full validation
- [ ] Manual CLI test for affected commands

## Service-Specific Notes

### MsActionTableService
- Complex serializer dependencies (xp20, xp24, xp33)
- State: `msactiontable_data: list[str]`
- Reset in `__enter__`: Clear `msactiontable_data`

### ActionTableService & ActionTableUploadService
- File I/O operations
- Reset in `__enter__`: Clear data buffers

### ConbusBlinkService & ConbusBlinkAllService
- Simple request/response pattern
- Minimal state

### ConbusDatapointService & ConbusDatapointQueryAllService
- Datapoint query/response handling
- Reset in `__enter__`: Clear response collections

### ConbusOutputService
- Output state management
- Reset in `__enter__`: Clear output state

### ConbusRawService
- Raw telegram handling
- Minimal changes needed

### ConbusScanService
- Scan state and progress
- Reset in `__enter__`: Clear discovered devices

### WriteConfigService
- Config write operations
- Reset in `__enter__`: Clear write state

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

def start_reactor(self) -> None:
    self.conbus_protocol.start_reactor()
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

### Final
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

**Common Issues**

| Issue                        | Cause                                     | Fix                                            |
|------------------------------|-------------------------------------------|------------------------------------------------|
| Cannot resolve Service       | Missing registration in dependencies.py   | Add service registration before use            |
| Signal connection TypeError  | Handler signature mismatch                | Check signal definition in ConbusEventProtocol |
| Memory leak                  | Signals not disconnected                  | Verify `__exit__` calls all `.disconnect()`    |
| State persists between calls | State not reset in `__enter__`            | Reset all mutable state                        |

## Success Criteria

- [ ] All 12 services migrated
- [ ] All quality checks pass (`pdm check`)
- [ ] All tests pass (`pdm test`)
- [ ] No breaking changes to CLI commands
- [ ] All services use ConbusEventProtocol
- [ ] No services inherit from ConbusProtocol
- [ ] Signal connections/disconnections verified
- [ ] Context managers tested
- [ ] ConbusProtocol registration removed from dependencies.py