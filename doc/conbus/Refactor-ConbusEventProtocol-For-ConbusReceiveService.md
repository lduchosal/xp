# Migration: ConbusReceiveService to ConbusEventProtocol

## Context
Migrate ConbusReceiveService from inheritance-based ConbusProtocol to composition-based ConbusEventProtocol pattern.

**Reference Implementation**: ConbusDiscoverService (src/xp/services/conbus/conbus_discover_service.py:20)
**Target File**: src/xp/services/conbus/conbus_receive_service.py:18

## Critical Notes
- **Signal Type**: on_telegram_sent emits `str`, not `bytes` - current signature already correct
- **Reactor Lifecycle**: timeout() does NOT call stop_reactor() - protocol handles it automatically
- **Start Pattern**: start() method does NOT call start_reactor() - caller's responsibility
- **CLI Update Required**: Command must explicitly call service.start_reactor() after service.start()
- **Context Manager**: Service needs __enter__/__exit__ since it won't inherit from ConbusProtocol
- **Scope**: Maintain singleton scope in dependency container registration

## Old Pattern (Inheritance)
- Service inherits from ConbusProtocol
- Override methods: connection_established(), telegram_sent(), telegram_received(), timeout(), failed()
- Tight coupling, difficult reuse
- Direct reactor management

## New Pattern (Composition + Signals)
- Service accepts ConbusEventProtocol via constructor injection
- Connect to signals using psygnal library
- Loose coupling, better testability
- Delegated reactor control

## Implementation Checklist

### 1. Constructor Refactoring
- [ ] Remove inheritance from ConbusProtocol
- [ ] Accept ConbusEventProtocol as constructor parameter
- [ ] Store protocol reference as instance variable
- [ ] Remove direct cli_config and reactor parameters
- [ ] Keep existing response model and callbacks initialization
- [ ] Rename connection_established() to connection_made() (signal-compatible name)

### 2. Signal Connection
- [ ] Connect to on_connection_made signal (replaces connection_established override)
- [ ] Connect to on_telegram_sent signal (replaces telegram_sent override)
- [ ] Connect to on_telegram_received signal (replaces telegram_received override)
- [ ] Connect to on_timeout signal (replaces timeout override)
- [ ] Connect to on_failed signal (replaces failed override)

### 3. Method Signature Updates
- [ ] telegram_sent() already accepts str parameter (matches ConbusEventProtocol.on_telegram_sent signal)
- [ ] Keep telegram_received() accepting TelegramReceivedEvent parameter
- [ ] Update timeout() to return None instead of bool (no longer controls reactor)
- [ ] Keep failed() accepting str parameter

### 4. Start Method Updates
- [ ] Keep start() method with same signature: (progress_callback, finish_callback, timeout_seconds)
- [ ] Remove start_reactor() call from start() method body
- [ ] start() only sets callbacks and timeout, doesn't start reactor
- [ ] Caller must explicitly call service.start_reactor() after start()
- [ ] Add start_reactor() convenience method that delegates to protocol.start_reactor()

### 5. Reactor Control and Lifecycle
- [ ] timeout() method no longer calls reactor.stop() (protocol handles it automatically)
- [ ] Update timeout() return type from bool to None
- [ ] failed() method doesn't need to stop reactor either
- [ ] Protocol manages reactor lifecycle based on timeout signal

### 6. Service Registration
- [ ] Update ServiceContainer registration in src/xp/utils/dependencies.py:333
- [ ] Replace cli_config and reactor parameters with conbus_protocol parameter
- [ ] Inject ConbusEventProtocol dependency from container
- [ ] Use factory lambda: `lambda: ConbusReceiveService(conbus_protocol=...)`
- [ ] Maintain singleton scope

### 7. Context Manager Support
- [ ] Add __enter__() method that returns self
- [ ] Add __exit__() method (can be empty or cleanup if needed)
- [ ] Ensure CLI command's `with service:` statement continues to work

### 8. Command Layer Updates
- [ ] Update CLI command: src/xp/cli/commands/conbus/conbus_receive_commands.py:55-60
- [ ] Add explicit `service.start_reactor()` call after `service.start()` line 59
- [ ] Pattern: `service.start(progress, on_finish, timeout)` then `service.start_reactor()`
- [ ] Verify context manager usage (`with service:`) still works with new implementation
- [ ] No changes to command user interface required (transparent to users)

### 9. Quality Validation
- [ ] Run `pdm typecheck` - verify all type hints correct
- [ ] Run `pdm lint` - ensure code style compliance
- [ ] Run `pdm format` - apply Black formatting
- [ ] Run `pdm test-quick` - validate tests pass
- [ ] Verify 75% minimum test coverage maintained
- [ ] Run `pdm check` - full quality validation

### 10. Testing Updates
- [ ] Create unit tests: tests/unit/test_services/test_conbus_receive_service.py
- [ ] Mock ConbusEventProtocol in unit tests using fixtures
- [ ] Test signal connections are properly established in __init__
- [ ] Test connection_made() method behavior
- [ ] Test telegram_received() updates response and calls progress callback
- [ ] Test timeout() calls finish callback with success=True
- [ ] Test failed() calls finish callback with error message
- [ ] Update integration tests: tests/integration/test_conbus_receive_integration.py
- [ ] Verify 75% minimum test coverage maintained

## Key Differences Summary

### Lifecycle Management
- Old: Service controls lifecycle via override methods
- New: Protocol emits signals, service handles events

### Coupling
- Old: Inheritance creates tight coupling to protocol internals
- New: Composition allows dependency injection and mocking

### Testability
- Old: Must instantiate full protocol stack for testing
- New: Mock protocol interface, test service in isolation

### Reusability
- Old: Cannot reuse protocol with multiple services simultaneously
- New: Single protocol instance can notify multiple subscribers

## References
- **Architecture**: doc/Architecture.md - Dependency injection patterns
- **Coding**: doc/Coding.md - Type safety, error handling, service patterns
- **Quality**: doc/Quality.md - Validation commands and coverage requirements
- **Reference**: src/xp/services/conbus/conbus_discover_service.py - Complete migration example
- **Protocol**: src/xp/services/protocol/conbus_event_protocol.py - Signal interface
