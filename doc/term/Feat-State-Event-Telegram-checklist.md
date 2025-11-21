# State Event Telegram Implementation Checklist

Reference: `doc/term/Feat-State-Event-Telegram.md`

## Prerequisites
- [ ] Read `doc/Quality.md` - Quality standards and checks
- [ ] Read `doc/Coding.md` - Type safety, documentation, naming conventions
- [ ] Read `doc/Architecture.md` - Layer architecture, DI patterns, signal-based communication

## Implementation Tasks

### 1. Model Updates
- [ ] Verify `ModuleState` has `link_number` field
- [ ] Confirm `EventTelegram` parses output events (input_number 80-83)

### 2. Service Layer - StateMonitorService
- [ ] Add `_find_module_by_link(link_number: int) -> Optional[ModuleState]`
- [ ] Add `_update_output_bit(module_state, output_number, output_state)`
- [ ] Add `_handle_event_telegram(event: TelegramReceivedEvent)`
- [ ] Extend `_on_telegram_received()` to route EVENT telegram type
- [ ] Validate XP24 module type (code 7) in event handler
- [ ] Filter output events (input_number 80-83 only)
- [ ] Update timestamp on output state changes
- [ ] Emit `on_module_state_changed` signal

### 3. Output State Format
- [ ] Parse space-separated format: `"0 1 0 0"`
- [ ] Handle empty outputs string
- [ ] Handle outputs shorter than output_number
- [ ] Convert boolean state to "0"/"1" string

### 4. Type Safety
- [ ] All methods have complete type hints
- [ ] Use `Optional[ModuleState]` for nullable returns
- [ ] Import `ModuleTypeCode` from models
- [ ] Pass `pdm typecheck`

### 5. Documentation
- [ ] Module docstring in modified files
- [ ] Method docstrings with Args/Returns
- [ ] Inline comments for output encoding logic (80-83 → 0-3)

### 6. Error Handling
- [ ] Handle malformed event telegrams (return early)
- [ ] Handle unknown link numbers (log debug, ignore)
- [ ] Handle non-XP24 events (ignore silently)
- [ ] Handle input events I00-I09 (ignore)
- [ ] Log debug messages for processed events

### 7. Testing - Unit Tests
- [ ] Test `_find_module_by_link()` with valid/invalid links
- [ ] Test `_update_output_bit()` for all outputs (0-3)
- [ ] Test `_update_output_bit()` with empty outputs string
- [ ] Test `_handle_event_telegram()` with XP24 output event
- [ ] Test ignore non-XP24 events
- [ ] Test ignore input events (I00-I09)
- [ ] Test signal emission on state change
- [ ] Mock `TelegramService.parse_event_telegram()`
- [ ] Minimum 75% coverage maintained

### 8. Testing - Integration Tests
- [ ] Test with XP24ServerService emulator
- [ ] Enable auto-report in test config
- [ ] Send action request, verify event telegram
- [ ] Verify module state updates from event
- [ ] Test multiple outputs changing
- [ ] Test multiple XP24 modules by link number

### 9. Quality Checks
- [ ] `pdm lint` - Ruff linting passes
- [ ] `pdm format` - Black formatting applied
- [ ] `pdm typecheck` - Mypy strict mode passes
- [ ] `pdm absolufy` - Absolute imports
- [ ] `pdm test-quick` - Fast tests pass
- [ ] `pdm check` - All quality checks pass

### 10. Edge Cases Validated
- [ ] Event telegram without matching link_number
- [ ] Input event telegram (I00-I09) ignored
- [ ] Non-XP24 module type ignored
- [ ] Malformed telegram handled gracefully
- [ ] Unknown output number logged and ignored
- [ ] Module without auto-report (no events expected)

## Architecture Compliance

### Dependency Injection
- [ ] No direct instantiation of services
- [ ] Dependencies injected via constructor
- [ ] Use `self.logger = logging.getLogger(__name__)`

### Signal-Based Communication
- [ ] Use psygnal signals for widget updates
- [ ] Emit `on_module_state_changed` after state update
- [ ] No direct widget access from service

### Layer Separation
- [ ] Service layer handles business logic only
- [ ] No UI concerns in StateMonitorService
- [ ] Protocol events transformed to service-level signals

## Logging
- [ ] DEBUG: Event telegram received with details
- [ ] DEBUG: Output state updated for module
- [ ] DEBUG: Event ignored with reason (wrong type, link, etc.)
- [ ] No sensitive data in logs

## Documentation Updates
- [ ] Update class docstring if behavior changes
- [ ] Update method docstrings for new methods
- [ ] No redundant comments

## Pre-Commit
- [ ] Run `pdm check` - all quality checks pass
- [ ] Review git diff for unintended changes
- [ ] Commit message follows convention
