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

---

**Output**: JSON sorted by module count (descending)
```json
{
  "events": {
    "XP20 10 00": ["A3", "A4"],
    "XP20 10 08": ["A3", "A4"]
  }
}
```

---

## Implementation Checklist

### 1. Service: `ConbusEventListService`
**Reference**: `ConbusDiscoverService` (src/xp/services/conbus/conbus_discover_service.py)

- [ ] Constructor: Accept `ConsonModuleListConfig` via DI (no protocol needed - pure parsing)
- [ ] Logger: `self.logger = logging.getLogger(__name__)`
- [ ] Public method: `list_events() -> Dict[str, List[str]]`
- [ ] Parse action tables: Extract module_type, link, input from each action
- [ ] Convert to event key: Format as `{module_type} {link:02d} {input:02d}`
- [ ] Group modules by event: Build dict mapping event → list of module names
- [ ] Sort by count: Order events by number of assigned modules (descending)
- [ ] Return result: Dict with events and their assigned modules

### 2. CLI Command: `xp conbus event list`
**Reference**: doc/architecture.md → Layer 1: CLI/API

- [ ] Location: Add to existing `src/xp/cli/commands/conbus/conbus_event_commands.py`
- [ ] Decorator: `@conbus_event.command("list")` with help text
- [ ] No parameters: Command takes no arguments
- [ ] Resolve service: `ctx.obj["container"].container.resolve(ConbusEventListService)`
- [ ] Output: Print events as JSON with `click.echo(json.dumps(result, indent=2))`
- [ ] No business logic: Delegate all work to service

### 3. Dependency Injection
**Reference**: src/xp/utils/dependencies.py

- [ ] Import: Add `ConbusEventListService` to imports
- [ ] Register service: Add to `_register_services()`
- [ ] Factory: Inject `ConsonModuleListConfig` dependency
- [ ] Scope: `punq.Scope.singleton`

### 4. Type Safety
**Reference**: doc/coding.md → Type Safety

- [ ] Type hints: All function parameters and return types
- [ ] Return type: `Dict[str, List[str]]` for event mapping
- [ ] No `Any`: Use specific types (`str`, `int`, `Dict`, `List`)
- [ ] Pass: `pdm typecheck` (mypy strict mode)

### 5. Documentation
**Reference**: doc/coding.md → Documentation

- [ ] Module docstring: Purpose and usage at top of service file
- [ ] Class docstring: Service purpose and attributes
- [ ] Method docstrings: Args, Returns for public methods
- [ ] CLI help: Docstring becomes help text in command

### 6. Error Handling
**Reference**: doc/coding.md → Error Handling

- [ ] Specific exceptions: Handle YAML parsing errors, missing config
- [ ] Logging: `self.logger.error(f"Failed: {e}")` with context
- [ ] Graceful degradation: Return empty dict on error, log details
- [ ] User-friendly: Clear error messages in CLI output

### 7. Testing
**Reference**: doc/quality.md, doc/coding.md → Testing

- [ ] Test file: `tests/unit/test_services/test_conbus_event_list_service.py`
- [ ] Mock config: Mock `ConsonModuleListConfig` with test data
- [ ] Test cases: Empty config, single module, multiple modules, duplicate events
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
- **Grouping Logic**: Single event can have multiple modules assigned
- **Sorting**: Display most-used events first (helps identify common buttons)
- **Config Source**: Uses existing `ConsonModuleListConfig` from DI container

---

## References

- **Architecture**: doc/architecture.md → DI, Layer separation
- **Coding Standards**: doc/coding.md → Type safety, naming, error handling
- **Quality**: doc/quality.md → Testing, coverage, type checking
- **Example**: src/xp/services/conbus/conbus_discover_service.py (DI pattern)
- **Config Model**: src/xp/models/homekit/homekit_conson_config.py
