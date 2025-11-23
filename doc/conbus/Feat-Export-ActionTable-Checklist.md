# Export ActionTable Implementation Checklist

## Service Layer

### ConbusExportActionTableService
- [ ] Create service in `src/xp/services/conbus/`
- [ ] Inject dependencies: `CliConfig`, `Reactor`, `ActionTableSerializer`, `TelegramService`, `ConsonConfigLoader`
- [ ] Implement `start(export_file: str)` method
- [ ] Load export.yml using `ConsonConfigLoader`
- [ ] Extract devices with serial numbers from loaded config
- [ ] Implement sequential action table download queue
- [ ] Track state: `current_device_index`, `actiontable_download_complete`, `actiontable_failed`
- [ ] Implement `_download_next_actiontable()` method
- [ ] Create `ActionTableService` instance per device
- [ ] Register callbacks: progress, finish, error
- [ ] Implement `_on_actiontable_finish(serial_number, actiontable_short)` callback
- [ ] Remove semicolons from actiontable_short entries
- [ ] Update device config's `action_table` field
- [ ] Mark device as complete and download next or finalize
- [ ] Implement `_on_actiontable_error(serial_number, error)` callback
- [ ] Log warning for failed downloads
- [ ] Mark device as failed without action_table field
- [ ] Continue to next device
- [ ] Implement `_finalize_export()` method
- [ ] Build updated `ConsonModuleListConfig` from module_configs
- [ ] Write back to export.yml using Pydantic serialization
- [ ] Return `ConbusExportResponse` with counts and status

### Response Model
- [ ] Enhance `ConbusExportResponse` dataclass
- [ ] Add `actiontable_count: int` field
- [ ] Add `actiontable_failed: int` field
- [ ] Update `export_status` values: OK, PARTIAL_ACTIONTABLE

### Error Handling
- [ ] Handle action table download timeout gracefully
- [ ] Handle connection refused gracefully
- [ ] Handle invalid action table data gracefully
- [ ] Empty action tables stored as empty list
- [ ] Failed downloads omit action_table field
- [ ] Errors don't fail entire export

### Progress Reporting
- [ ] Display "Loading export.yml..."
- [ ] Display "Found N devices"
- [ ] Display per-device progress: "Downloading action table X/N: name (serial)..."
- [ ] Display success: "✓ Action table: N entries"
- [ ] Display warnings: "⚠ Action table: timeout (skipped)"
- [ ] Display final summary: "Export updated: export.yml (X/N action tables downloaded)"
- [ ] Display estimated time for >10 devices

## CLI Layer

### Command Definition
- [ ] Create command in `src/xp/cli/commands/conbus/export_commands.py`
- [ ] Use `@export_group.command("actiontable")` decorator
- [ ] Add `--file` / `-f` option with default "export.yml"
- [ ] Use `@connection_command()` decorator
- [ ] Accept `ctx: click.Context` and `export_file: str`
- [ ] Write clear docstring with examples
- [ ] Resolve `ConbusExportActionTableService` from container
- [ ] Call `service.start(export_file)`
- [ ] No business logic in command

## Type Safety

### Type Hints
- [ ] All function parameters fully typed
- [ ] All return types specified
- [ ] Use `Optional[T]` for nullable types
- [ ] Use `List[str]`, `Dict[str, Any]` for collections
- [ ] Use `Set[str]` for tracking sets
- [ ] No `Any` unless necessary

### Pass Mypy
- [ ] Run `pdm run typecheck` and fix all errors
- [ ] Strict mode compliance (no untyped defs)

## Documentation

### Docstrings
- [ ] Module-level docstring at top of service file
- [ ] Service class docstring with purpose
- [ ] All public methods have docstrings
- [ ] Args, Returns, Raises documented
- [ ] Inline comments for complex logic only

## Testing

### Unit Tests
- [ ] Create test file `tests/unit/test_services/test_conbus_export_actiontable_service.py`
- [ ] Test loading export.yml with ConsonConfigLoader
- [ ] Test sequential download queue processing
- [ ] Test `_on_actiontable_finish()` updates device config
- [ ] Test semicolon removal from actiontable_short
- [ ] Test `_on_actiontable_error()` marks failed without action_table
- [ ] Test export includes action_table when present
- [ ] Test export omits action_table when failed
- [ ] Test export_status values: OK, PARTIAL_ACTIONTABLE
- [ ] Test writing updated YAML using Pydantic serialization
- [ ] Mock ActionTableService for unit tests
- [ ] Mock ConsonConfigLoader for unit tests
- [ ] Minimum 75% coverage

### Integration Tests
- [ ] Test full export actiontable workflow with real files
- [ ] Test YAML round-trip with action tables
- [ ] Test multi-device export with mixed success/failure
- [ ] Test action table download timeout handling
- [ ] Use XP server emulators if needed

## Code Quality

### Run Quality Checks
- [ ] `pdm run typecheck` - mypy passes
- [ ] `pdm run flake8` - code quality passes
- [ ] `pdm run interrogate` - documentation passes
- [ ] `pdm run refurb` - modernization passes
- [ ] `pdm test-quick` - tests pass
- [ ] `pdm absolufy` - absolute imports
- [ ] `pdm lint` - ruff passes
- [ ] `pdm format` - black formatting applied
- [ ] `pdm check` - all quality checks pass

### Code Style
- [ ] Line length: 88 characters max
- [ ] Absolute imports only
- [ ] Import order: stdlib → third-party → local
- [ ] Multi-line imports with trailing comma
- [ ] No commented-out code
- [ ] No unused imports or variables

### Naming Conventions
- [ ] Service class: `ConbusExportActionTableService` (PascalCase)
- [ ] Public methods: `snake_case`
- [ ] Private methods: `_leading_underscore`
- [ ] Constants: `UPPER_SNAKE_CASE`

## Service Container

### Registration
- [ ] Register `ConbusExportActionTableService` in `ServiceContainer._register_services()`
- [ ] Use factory lambda for registration
- [ ] Singleton scope
- [ ] All dependencies injected via constructor

## Logging

### Logger Setup
- [ ] Initialize logger: `self.logger = logging.getLogger(__name__)`
- [ ] Log at INFO level for key operations (start, device progress, completion)
- [ ] Log at ERROR level for failures
- [ ] Log at DEBUG level for verbose details
- [ ] Use f-strings with context
- [ ] No sensitive data in logs

## Dependencies

### Reuse Existing Components
- [ ] Use `ActionTableService` for downloads (existing)
- [ ] Use `ActionTableSerializer` for deserialization (existing)
- [ ] Use `ConsonConfigLoader` for loading export.yml (existing)
- [ ] Use `ConsonModuleListConfig` model (existing)
- [ ] Use `ConsonModuleConfig` model with existing `action_table` field
- [ ] No new external packages required

## References
- [ ] Review `doc/conbus/Feat-Export.md` for export patterns
- [ ] Review `src/xp/cli/commands/conbus/actiontable/actiontable_download_commands.py` for CLI patterns
- [ ] Review `src/xp/cli/commands/conbus/export_commands.py` for export command patterns
- [ ] Review `src/xp/services/conbus/actiontable/actiontable_download_service.py` for ActionTableService usage
- [ ] Follow quality standards in `doc/Quality.md`
- [ ] Follow coding standards in `doc/Coding.md`
- [ ] Follow architecture patterns in `doc/Architecture.md`
