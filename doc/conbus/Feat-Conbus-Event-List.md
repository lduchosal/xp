# Conbus Event List

List configured event telegrams from module action tables.

## Specification

**CLI**: `xp conbus event list`

Reads `conson.yml` (via DI injected `ConsonModuleListConfig`), parses action tables, converts to event telegrams, and groups by event with assigned modules.

---

**Input**: Action table from conson.yml
Example conson.yml:
```yaml
- name: A3
  action_table:
    - XP20 10 0 > 0 OFF
    - XP20 10 8 > 0 ON
- name: A4
  action_table:
    - XP20 10 0 > 0 OFF
    - XP20 10 8 > 0 ON
```

**Action Format**: `{module_type} {link} {input} > {output} {action}`
- **Event Key**: Only left side used: `{module_type} {link:02d} {input:02d}`
- **Ignored**: Everything after `>` symbol (output/action)
- **Module Type**: Use name string directly (e.g., "XP20", "CP20")

---

**Output**: JSON wrapped in "events" key, sorted by module count (descending)
```json
{
  "events": {
    "CP20 00 00": ["A1", "A2", "A3", "A4", "A5", "A6", "A7"],
    "XP20 10 00": ["A3", "A4", "A5"],
    "XP20 10 08": ["A3", "A4"],
    "XP33 05 02": ["A1"]
  }
}
```

---

## Implementation Checklist

### 1. Model: `ConbusEventListResponse`
**Reference**: `ConbusDiscoverResponse` (src/xp/models/conbus/conbus_discover.py)

- [ ] Location: `src/xp/models/conbus/conbus_event_list.py`
- [ ] Dataclass with fields:
  - `events: Dict[str, List[str]]` - Event mapping (event_key → module names)
  - `timestamp: datetime` - Response timestamp
- [ ] Method: `to_dict() -> Dict[str, Any]` for JSON serialization
- [ ] Add to: `src/xp/models/__init__.py` exports

### 2. Service: `ConbusEventListService`
**Reference**: `ConbusDiscoverService` (src/xp/services/conbus/conbus_discover_service.py)

- [ ] Constructor: Accept `ConsonModuleListConfig` via DI (no protocol needed - pure parsing)
- [ ] Logger: `self.logger = logging.getLogger(__name__)`
- [ ] Public method: `list_events() -> ConbusEventListResponse`
- [ ] Use existing parser: `ActionTableSerializer.parse_action_string()` for each action
  - **Reuse**: Parsing logic already tested in actiontable_serializer
  - **Error handling**: Catches ValueError for invalid format (log warning, skip)
- [ ] Extract event data: From parsed ActionTableEntry get `module_type.name`, `link_number`, `module_input`
- [ ] Convert to event key: Format as `f"{module_type.name} {link:02d} {input:02d}"` (space-separated)
- [ ] Deduplicate: Each module listed ONCE per unique event (use set, then list)
- [ ] Group modules by event: Build dict mapping event → list of module names
- [ ] Sort by count: Order events by number of assigned modules (descending)
- [ ] Skip empty modules: Silent skip if no action_table or empty list
- [ ] Return response: `ConbusEventListResponse(events=events_dict)`

### 3. CLI Command: `xp conbus event list`
**Reference**: doc/architecture.md → Layer 1: CLI/API

- [ ] Location: Add to existing `src/xp/cli/commands/conbus/conbus_event_commands.py`
- [ ] Decorator: `@conbus_event.command("list")` with help text
- [ ] No parameters: Command takes no arguments
- [ ] Resolve service: `ctx.obj["container"].container.resolve(ConbusEventListService)`
- [ ] Call service: `response = service.list_events()`
- [ ] Output: Print as JSON with `click.echo(json.dumps(response.to_dict(), indent=2))`
- [ ] No business logic: Delegate all work to service

### 4. Dependency Injection
**Reference**: src/xp/utils/dependencies.py

- [ ] Import: Add `ConbusEventListService` to imports
- [ ] Register service: Add to `_register_services()`
- [ ] Factory: Inject `ConsonModuleListConfig` dependency
- [ ] Scope: `punq.Scope.singleton`

### 5. Type Safety
**Reference**: doc/coding.md → Type Safety

- [ ] Type hints: All function parameters and return types
- [ ] Return type: `ConbusEventListResponse` (dataclass model)
- [ ] No `Any`: Use specific types (`str`, `int`, `Dict`, `List`, `ActionTableEntry`)
- [ ] Pass: `pdm typecheck` (mypy strict mode)

### 6. Documentation
**Reference**: doc/coding.md → Documentation

- [ ] Module docstring: Purpose and usage at top of service file
- [ ] Class docstring: Service purpose and attributes
- [ ] Method docstrings: Args, Returns for public methods
- [ ] CLI help: Docstring becomes help text in command

### 7. Error Handling
**Reference**: doc/coding.md → Error Handling

- [ ] Catch parsing errors: `ActionTableSerializer.parse_action_string()` raises ValueError
- [ ] Log invalid actions: `logger.warning(f"Invalid action '{action}': {e}")`, continue
- [ ] Skip empty modules: Silent skip if module has no action_table or empty list
- [ ] Handle config errors: Catch exceptions, return empty response with error log
- [ ] Logging: `self.logger.error(f"Failed: {e}")` with context
- [ ] Graceful degradation: Return `ConbusEventListResponse(events={})`
- [ ] User-friendly: Clear error messages in CLI output

### 8. Testing
**Reference**: doc/quality.md, doc/coding.md → Testing

- [ ] Test file: `tests/unit/test_services/test_conbus_event_list_service.py`
- [ ] Mock config: Mock `ConsonModuleListConfig` with test data
- [ ] Test cases:
  - Empty config (no modules)
  - Single module with one action
  - Multiple modules sharing same event
  - Duplicate actions in same module (deduplication)
  - Invalid action format (skipped with warning)
  - Empty action_table (silently skipped)
  - Sorting by module count
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

## Key Implementation Notes

- **No Protocol**: Pure parsing service, no TCP/event communication needed
- **Stateless**: Pure function transformation of config → event mapping
- **Reuse Existing**: Use `ActionTableSerializer.parse_action_string()` for parsing
  - Already handles: Regex validation, error handling, all edge cases
  - Already tested: See `tests/unit/test_services/test_actiontable_serializer.py`
  - Don't reinvent: Parsing logic is proven and comprehensive
- **Extract Event Data**: From `ActionTableEntry` get `module_type.name`, `link_number`, `module_input`
- **Event Key Format**: `f"{module_type.name} {link:02d} {input:02d}"` (space-separated string)
- **Module Type**: Use enum name string directly ("XP20", "CP20"), not numeric code
- **Deduplication**: Each module appears ONCE per unique event (use set → list)
- **Grouping Logic**: Single event can have multiple modules assigned
- **Sorting**: Display most-used events first (helps identify common buttons)
- **Error Handling**: ActionTableSerializer raises ValueError, catch and skip with warning
- **Return Format**: `ConbusEventListResponse` model with `events` dict and timestamp
- **Config Source**: Uses existing `ConsonModuleListConfig` from DI container

---

## References

- **Architecture**: doc/architecture.md → DI, Layer separation
- **Coding Standards**: doc/coding.md → Type safety, naming, error handling
- **Quality**: doc/quality.md → Testing, coverage, type checking
- **Service Pattern**: src/xp/services/conbus/conbus_discover_service.py (DI, response model)
- **Config Model**: src/xp/models/homekit/homekit_conson_config.py
- **Parser (Reuse)**: src/xp/services/actiontable/actiontable_serializer.py (`parse_action_string()`)
- **Parser Tests**: tests/unit/test_services/test_actiontable_serializer.py (edge cases covered)
