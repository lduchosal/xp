# Migration: ConbusReceiveService to ConbusEventProtocol

## TL;DR
Refactor ConbusReceiveService from inheritance (ConbusProtocol) to composition (ConbusEventProtocol + signals). **Key changes**: Constructor takes protocol parameter, connect to signals instead of overriding methods, CLI command must call `start_reactor()` explicitly.

**Estimated Time**: 2-3 hours
**Order**: Follow sections sequentially (1→10)

## ⚠️ CRITICAL: Read This First

### Breaking Changes
1. **CLI Update Required**: Command MUST add explicit `service.start_reactor()` call after `service.start()` (line 59)
2. **Context Manager**: Service MUST implement `__enter__`/`__exit__` (no longer inherited from ConbusProtocol)
3. **Method Signature**: timeout() changes from `-> bool` to `-> None`
4. **Constructor**: Takes `ConbusEventProtocol` instead of `ConbusClientConfig` + `reactor`

### Common Mistakes to Avoid
- ❌ DON'T call stop_reactor() in timeout() - protocol handles it automatically
- ❌ DON'T call start_reactor() in start() method body - caller's responsibility
- ❌ DON'T use bytes for telegram_sent parameter - signal emits `str`
- ❌ DON'T forget to disconnect signals in __exit__ - causes memory leaks
- ✅ DO set timeout on protocol instance: `self.conbus_protocol.timeout_seconds = timeout_seconds`
- ✅ DO reset state in __enter__ to handle singleton reuse
- ✅ DO maintain singleton scope in container registration

## Context

Migrate ConbusReceiveService from inheritance-based ConbusProtocol to composition-based ConbusEventProtocol pattern.

**Reference Implementation**: ConbusDiscoverService (src/xp/services/conbus/conbus_discover_service.py:20)
**Target File**: src/xp/services/conbus/conbus_receive_service.py:18

### Old Pattern (Inheritance)
```python
class ConbusReceiveService(ConbusProtocol):
    def __init__(self, cli_config: ConbusClientConfig, reactor: PosixReactorBase):
        super().__init__(cli_config, reactor)
        self.receive_response = ConbusReceiveResponse(success=True)

    def connection_established(self) -> None:
        self.logger.debug("Connection established")

    def timeout(self) -> bool:
        self.receive_response.success = True
        return False  # Stop reactor
```

**Problems**: Tight coupling, difficult reuse, hard to test

### New Pattern (Composition + Signals)
```python
class ConbusReceiveService:
    def __init__(self, conbus_protocol: ConbusEventProtocol):
        self.conbus_protocol = conbus_protocol
        self.receive_response = ConbusReceiveResponse(success=True)

        # Connect to signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_timeout.connect(self.timeout)

    def connection_made(self) -> None:
        self.logger.debug("Connection established")

    def timeout(self) -> None:  # No return value
        self.receive_response.success = True
        # Protocol handles reactor stop automatically
```

**Benefits**: Loose coupling, dependency injection, better testability

## Implementation Checklist

### 1. Constructor Refactoring [CRITICAL - DO FIRST]
- [ ] Remove inheritance: `class ConbusReceiveService(ConbusProtocol)` → `class ConbusReceiveService`
- [ ] Update constructor signature: Accept `conbus_protocol: ConbusEventProtocol` parameter
- [ ] Remove `cli_config` and `reactor` parameters from constructor
- [ ] Store protocol reference: `self.conbus_protocol = conbus_protocol`
- [ ] Keep existing response model initialization: `self.receive_response`
- [ ] Keep callback initialization: `self.progress_callback`, `self.finish_callback`
- [ ] Rename method: `connection_established()` → `connection_made()`

### 2. Signal Connection [CRITICAL]
Connect event handlers in `__init__` after storing protocol reference:
- [ ] `self.conbus_protocol.on_connection_made.connect(self.connection_made)`
- [ ] `self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)`
- [ ] `self.conbus_protocol.on_telegram_received.connect(self.telegram_received)`
- [ ] `self.conbus_protocol.on_timeout.connect(self.timeout)`
- [ ] `self.conbus_protocol.on_failed.connect(self.failed)`

### 3. Method Updates [IMPORTANT]
- [ ] **telegram_sent(telegram_sent: str)** - Already correct, accepts `str` parameter
- [ ] **telegram_received(telegram_received: TelegramReceivedEvent)** - No changes needed
- [ ] **timeout()** - Update return type: `-> bool` to `-> None`
- [ ] **timeout()** - Remove `return False` statement
- [ ] **timeout()** - Remove any `reactor.stop()` calls (protocol handles automatically)
- [ ] **failed(message: str)** - No changes needed, no reactor stop required

### 4. Start Method and Timeout Handling [IMPORTANT]
Update `start()` method behavior:
- [ ] Keep method signature: `start(progress_callback, finish_callback, timeout_seconds)`
- [ ] Set callbacks: `self.progress_callback = progress_callback`
- [ ] Set finish callback: `self.finish_callback = finish_callback`
- [ ] Set timeout on protocol: `if timeout_seconds: self.conbus_protocol.timeout_seconds = timeout_seconds`
- [ ] **Remove** `self.start_reactor()` call from method body
- [ ] Add separate `start_reactor()` convenience method: `self.conbus_protocol.start_reactor()`

### 5. Context Manager Support [CRITICAL - BLOCKS CLI]
- [ ] Add `__enter__(self) -> "ConbusReceiveService"` method that returns `self`
- [ ] Reset state in __enter__: `self.receive_response = ConbusReceiveResponse(success=True)`
- [ ] Add `__exit__(self, _exc_type, _exc_val, _exc_tb) -> None` method
- [ ] Disconnect all signals in __exit__ to prevent memory leaks:
  ```python
  self._conbus_protocol.on_connection_made.disconnect(self.connection_made)
  self._conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
  self._conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
  self._conbus_protocol.on_timeout.disconnect(self.timeout)
  self._conbus_protocol.on_failed.disconnect(self.failed)
  ```
- [ ] Verify CLI command's `with service:` statement continues to work

### 6. Service Registration [CRITICAL - BLOCKS CLI]
Update dependency injection in src/xp/utils/dependencies.py:333:
- [ ] Replace constructor parameters in factory lambda
- [ ] Change from: `ConbusReceiveService(cli_config=..., reactor=...)`
- [ ] Change to: `ConbusReceiveService(conbus_protocol=self.container.resolve(ConbusEventProtocol))`
- [ ] Maintain singleton scope: `scope=punq.Scope.singleton`
- [ ] Add proper type hint: `ConbusReceiveService` in register call

### 7. Command Layer Updates [CRITICAL - BLOCKS CLI]
Update src/xp/cli/commands/conbus/conbus_receive_commands.py:55-60:
- [ ] Add explicit `service.start_reactor()` call after `service.start()` on line 59
- [ ] Updated pattern:
  ```python
  with service:
      service.init(progress, on_finish, timeout)
      service.start_reactor()  # ADD THIS LINE
  ```
- [ ] Verify context manager usage still works
- [ ] Verify command interface remains unchanged for users

### 8. Quality Validation [IMPORTANT]
Run all quality checks:
- [ ] `pdm typecheck` - Verify all type hints correct
- [ ] `pdm lint` - Ensure code style compliance
- [ ] `pdm format` - Apply Black formatting
- [ ] `pdm test-quick` - Validate unit tests pass
- [ ] `pdm check` - Full quality validation suite
- [ ] Verify 75% minimum test coverage maintained

### 9. Unit Testing [IMPORTANT - PREVENTS REGRESSION]
Create tests/unit/test_services/test_conbus_receive_service.py:
- [ ] Create fixture for mock ConbusEventProtocol
- [ ] Test signal connections established in `__init__`
- [ ] Test `connection_made()` logs correctly
- [ ] Test `telegram_received()` updates response and calls progress_callback
- [ ] Test `telegram_received()` appends to received_telegrams list
- [ ] Test `timeout()` sets success=True and calls finish_callback
- [ ] Test `failed()` sets error message and calls finish_callback
- [ ] Test `start()` sets callbacks and timeout on protocol
- [ ] Test `start_reactor()` delegates to protocol
- [ ] Test `__enter__` resets state
- [ ] Test `__exit__` disconnects all signals

### 10. Edge Case and Integration Testing [IMPORTANT]
- [ ] Test edge case: `timeout_seconds=None` uses protocol default
- [ ] Test edge case: `progress_callback=None` doesn't crash on telegram_received
- [ ] Test edge case: `finish_callback=None` doesn't crash on timeout/failed
- [ ] Test multiple calls with singleton scope (state reset in __enter__)
- [ ] Update integration tests: tests/integration/test_conbus_receive_integration.py
- [ ] Run existing integration tests to verify no regression
- [ ] Test CLI command: `xp conbus receive 2.0` works identically to before
- [ ] Verify signal disconnection prevents memory leaks in long-running processes

## Completion Criteria

### Must Pass
- [ ] All quality checks pass (section 8)
- [ ] `xp conbus receive` command works identically to before
- [ ] No breaking changes to public API or command interface
- [ ] All unit tests pass with 75%+ coverage
- [ ] Integration tests show no regression

### Verification Commands
```bash
# Quality checks
pdm check

# Test specific command
xp conbus receive 2.0

# Verify no regressions
pdm test-quick
```

## Troubleshooting

### Reactor doesn't stop after timeout
**Symptom**: Service hangs, never calls finish_callback
**Cause**: Signal not connected properly
**Fix**: Verify `self.conbus_protocol.on_timeout.connect(self.timeout)` in __init__
**Debug**: Add logging in timeout() to verify it's being called

### TypeError: 'bytes' object has no attribute
**Symptom**: TypeError when telegram_sent signal emits
**Cause**: Method signature mismatch - expecting bytes instead of str
**Fix**: Verify telegram_sent parameter type is `str`, not `bytes`
**Note**: Signal emits `str`, not `bytes`

### Service state persists between calls
**Symptom**: Previous received_telegrams appear in new requests
**Cause**: Singleton scope with mutable state not being reset
**Fix**: Reset `receive_response` in `__enter__` method
**Pattern**: `self.receive_response = ConbusReceiveResponse(success=True)`

### Memory leak in long-running process
**Symptom**: Memory grows over time with repeated calls
**Cause**: Signals not disconnected in __exit__
**Fix**: Add disconnect calls in `__exit__` for all signals
**Verify**: Monitor memory with repeated CLI calls

### Import errors after refactoring
**Symptom**: ModuleNotFoundError or ImportError
**Cause**: Missing import for ConbusEventProtocol
**Fix**: Add `from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol`
**Check**: Remove old imports of ConbusProtocol if unused

### Container resolution fails
**Symptom**: "Cannot resolve ConbusReceiveService" error
**Cause**: Factory lambda not updated in dependencies.py
**Fix**: Verify registration uses new constructor signature
**Debug**: Check ConbusEventProtocol is registered before ConbusReceiveService

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
- **Reference**: src/xp/services/conbus/conbus_discover_service.py:20 - Complete migration example
- **Protocol**: src/xp/services/protocol/conbus_event_protocol.py - Signal interface
