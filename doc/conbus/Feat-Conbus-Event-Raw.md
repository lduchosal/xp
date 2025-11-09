# Conbus Event Raw

Send raw event telegrams via CLI to simulate button presses on Conbus modules.

## Specification

**CLI**: `xp conbus event raw [module_type] [link_number] [input_number] [time_ms]`

**Parameters**:
- `module_type`: Module type code (e.g., `CP20`, `XP33`) → resolved to numeric code
- `link_number`: Link number `0-99`
- `input_number`: Input number `0-9`
- `time_ms`: Delay between MAKE/BREAK events (default: `1000ms`)
---

**Event Format**:
```
<E{module_type_code:02d}L{link_number:02d}I{input_number:02d}M{checksum}>
<E{module_type_code:02d}L{link_number:02d}I{input_number:02d}B{checksum}>
```
---

**Examples**:
- `xp conbus event raw CP20 00 00` → `<E02L00I00MAK>` + wait + `<E02L00I00BAK>`
- `xp conbus event raw XP33 00 00` → `<E33L00I00MAK>` + wait + `<E33L00I00BAK>`
---

**Progress output**:
```
{ "telegram": "<E27L02I82B>" }
```
---

**Finish output**:
The process finish by timing out.
```
{ 
  "received_telegrams": [
      "<E27L02I82B>",
      "<E27L02I82B>",
      "<E27L02I82B>"
  ],
  "success": true,
  "error": null,
  "timestamp": "2025-11-09T16:02:36.316766"
}
```

---

## Implementation Checklist

### 1. Service: `ConbusEventRawService`
**Reference**: `ConbusDiscoverService` (src/xp/services/conbus/conbus_discover_service.py)

- [ ] Constructor: Accept `ConbusEventProtocol` via DI
- [ ] Connect protocol signals to handlers:
  - [ ] `on_connection_made` → send first event telegram (MAKE) and schedule second event (BREAK) after delay
  - [ ] `on_telegram_received` → display on cli received telegrams 
  - [ ] `on_timeout` → handle clean finish
  - [ ] `on_failed` → handle connection failure
- [ ] Logger: `self.logger = logging.getLogger(__name__)`
- [ ] Result tracking: Create response model (success, sent_telegrams, received_telegrams, error)
- [ ] Callbacks: Support `finish_callback` for async completion
- [ ] Callbacks: Support `progress_callback` for async progress when event telegram are received
- [ ] Public method: `run(module_type, link_number, input_number, time_ms, finish_callback, timeout_seconds)`
- [ ] Reactor control: Call `start_reactor()` to begin, `stop_reactor()` when done/failed
- [ ] Event telegram format: Use `TelegramType.EVENT`, construct payload manually (not via `send_telegram`)

### 2. CLI Command: `xp conbus event raw`
**Reference**: doc/architecture.md → Layer 1: CLI/API

- [ ] Location: `src/xp/cli/commands/conbus_event.py`
- [ ] Register: Add to `cli/main.py` command group
- [ ] Decorator: `@click.command()` with help text
- [ ] Parameters: `module_type`, `link_number`, `input_number`, `time_ms` (default: `1000`)
- [ ] Resolve service: `ctx.obj["container"].container.resolve(ConbusEventRawService)`
- [ ] Convert module type: Use `MODULE_TYPE_REGISTRY` to get numeric code
- [ ] Validation: Check parameter ranges (link 0-99, input 0-9, time_ms > 0)
- [ ] Output: Print sent/received telegrams, handle errors with `click.echo()`
- [ ] No business logic: Delegate all work to service

### 3. Protocol Integration
**Reference**: `ConbusEventProtocol` (src/xp/services/protocol/conbus_event_protocol.py)

- [ ] Send event telegrams directly via `sendFrame()` (not `send_telegram()` - that's for System telegrams)
- [ ] Payload format: `E{module_code:02d}L{link:02d}I{input:02d}{M|B}`
- [ ] Checksum: Calculate via `calculate_checksum()` (from utils)
- [ ] Timing: Use `reactor.callLater(time_ms/1000, callback)` for BREAK event delay
- [ ] Queue: Always sdd telegrams to `telegram_queue` 

### 4. Type Safety
**Reference**: doc/coding.md → Type Safety

- [ ] Type hints: All function parameters and return types
- [ ] Models: Use Pydantic for request/response if complex
- [ ] No `Any`: Use specific types (`str`, `int`, `Optional[T]`)
- [ ] Pass: `pdm typecheck` (mypy strict mode)

### 5. Documentation
**Reference**: doc/coding.md → Documentation

- [ ] Module docstring: Purpose and usage at top of service file
- [ ] Class docstring: Service purpose and attributes
- [ ] Method docstrings: Args, Returns for public methods
- [ ] CLI help: Docstring becomes help text in command

### 6. Error Handling
**Reference**: doc/coding.md → Error Handling

- [ ] Specific exceptions: Not bare `Exception`
- [ ] Logging: `self.logger.error(f"Failed: {e}")` with context
- [ ] Response: Return result object with `success`, `data`, `error` fields
- [ ] Cleanup: Stop reactor in `finally` or failure handlers

### 7. Testing
**Reference**: doc/quality.md, doc/coding.md → Testing

- [ ] Test file: `tests/unit/test_services/test_conbus_event_raw_service.py`
- [ ] Mock protocol: Mock `ConbusEventProtocol` and its signals
- [ ] Test cases: Success path, timeout, connection failure, invalid parameters
- [ ] Coverage: Minimum 75%
- [ ] Run: `pdm test-quick` before commit

### 8. Quality Checks
**Reference**: doc/quality.md

- [ ] `pdm lint` - Ruff linting
- [ ] `pdm format` - Black formatting
- [ ] `pdm typecheck` - Mypy strict mode
- [ ] `pdm test-quick` - Fast tests
- [ ] `pdm check` - All quality checks

---

## Key Differences vs Discovery Service

- **Event vs System**: Send `TelegramType.EVENT` (not `SYSTEM`)
- **Queue send**: Use `send_telegram()` helper to always use queue
- **No response parsing**: Events don't expect replies (display as progress callback)
- **Timed sequence**: MAKE → wait → BREAK (not query → parse → query loop)
- **Simpler result**: Only track sent telegrams and receive events, no device discovery logic

---

## References

- **Architecture**: doc/architecture.md → Event-driven, DI, Layer separation
- **Coding Standards**: doc/coding.md → Type safety, naming, error handling
- **Quality**: doc/quality.md → Testing, coverage, type checking
- **Protocol**: src/xp/services/protocol/conbus_event_protocol.py
- **Example**: src/xp/services/conbus/conbus_discover_service.py