# Migration: ConbusReceiveService to ConbusEventProtocol

## Context
Migrate ConbusReceiveService from inheritance-based ConbusProtocol to composition-based ConbusEventProtocol pattern.

**Reference Implementation**: ConbusDiscoverService (src/xp/services/conbus/conbus_discover_service.py:20)
**Target File**: src/xp/services/conbus/conbus_receive_service.py:18

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

### 2. Signal Connection
- [ ] Connect to on_connection_made signal (replaces connection_established override)
- [ ] Connect to on_telegram_sent signal (replaces telegram_sent override)
- [ ] Connect to on_telegram_received signal (replaces telegram_received override)
- [ ] Connect to on_timeout signal (replaces timeout override)
- [ ] Connect to on_failed signal (replaces failed override)

### 3. Method Signature Updates
- [ ] Rename connection_established() to connection_made()
- [ ] Keep existing telegram_sent() signature
- [ ] Keep existing telegram_received() signature
- [ ] Keep existing timeout() signature
- [ ] Keep existing failed() signature

### 4. Reactor Control Delegation
- [ ] Replace direct reactor.start() with protocol.start_reactor()
- [ ] Replace direct reactor.stop() with protocol.stop_reactor()
- [ ] Remove return value from timeout() method
- [ ] Call stop_reactor() in timeout() method

### 5. Telegram Sending
- [ ] Use protocol.send_telegram() for sending telegrams
- [ ] Pass TelegramType, serial_number, SystemFunction, data_value parameters
- [ ] Remove direct sendFrame() calls if any

### 6. Service Registration
- [ ] Update ServiceContainer registration in src/xp/utils/dependencies.py
- [ ] Inject ConbusEventProtocol dependency
- [ ] Use factory lambda for service creation
- [ ] Ensure singleton scope if needed

### 7. Command Layer Updates
- [ ] Update CLI commands to resolve ConbusReceiveService from container
- [ ] Verify command still works with new service structure
- [ ] No changes to command interface required

### 8. Quality Validation
- [ ] Run `pdm typecheck` - verify all type hints correct
- [ ] Run `pdm lint` - ensure code style compliance
- [ ] Run `pdm format` - apply Black formatting
- [ ] Run `pdm test-quick` - validate tests pass
- [ ] Verify 75% minimum test coverage maintained
- [ ] Run `pdm check` - full quality validation

### 9. Testing Updates
- [ ] Mock ConbusEventProtocol in unit tests
- [ ] Verify signal connections in tests
- [ ] Test timeout behavior
- [ ] Test failure handling
- [ ] Test telegram reception

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
