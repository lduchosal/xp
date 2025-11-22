# Migration: ConbusProtocol to ConbusEventProtocol

## TL;DR
Migrate 12 services from inheritance-based `ConbusProtocol` to composition-based `ConbusEventProtocol`. **Key changes**: Constructor takes protocol parameter, connect to signals instead of overriding methods, no reactor lifecycle management in service.

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

#### 5. Public Methods (start/send_*)
- [ ] Keep method signatures unchanged
- [ ] Set timeout: `self.conbus_protocol.timeout_seconds = timeout_seconds`
- [ ] Remove `self.start_reactor()` from method body
- [ ] Add `start_reactor()` method: `self.conbus_protocol.start_reactor()`

#### 6. Context Manager
- [ ] Add `__enter__(self) -> "ServiceName"` returning `self`
- [ ] Reset state in `__enter__` (response models, buffers, etc.)
- [ ] Add `__exit__(self, ...)` disconnecting all signals
- [ ] Disconnect pattern:
  ```python
  self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
  self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
  self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
  self.conbus_protocol.on_timeout.disconnect(self.timeout)
  self.conbus_protocol.on_failed.disconnect(self.failed)
  ```

#### 7. Dependencies Registration
- [ ] Update factory in `src/xp/utils/dependencies.py`
- [ ] Change constructor parameters
- [ ] Before: `Service(cli_config=..., reactor=...)`
- [ ] After: `Service(conbus_protocol=self.container.resolve(ConbusEventProtocol))`
- [ ] Keep singleton scope: `punq.Scope.singleton`

#### 8. CLI Commands
- [ ] Add explicit `service.start_reactor()` after `service.start()` or `service.send_*()`
- [ ] Pattern:
  ```python
  with service:
      service.send_telegram(...)
      service.start_reactor()  # Add this
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

## Success Criteria

- [ ] All 12 services migrated
- [ ] All quality checks pass (`pdm check`)
- [ ] All tests pass (`pdm test`)
- [ ] No breaking changes to CLI commands
- [ ] All services use ConbusEventProtocol
- [ ] No services inherit from ConbusProtocol
- [ ] Signal connections/disconnections verified
- [ ] Context managers tested