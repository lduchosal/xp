# Coding Standards

## Type Safety
- [ ] All functions have complete type hints (parameters and return types)
- [ ] Use `Optional[T]` for nullable types
- [ ] Use `List[T]`, `Dict[K, V]` for collections (not bare `list`, `dict`)
- [ ] Pydantic models for all data structures
- [ ] No `Any` unless absolutely necessary
- [ ] Must pass `pdm typecheck` (mypy strict mode)

## Code Style
- [ ] Line length: 88 characters (Black formatter)
- [ ] Imports: Absolute imports only (use `pdm absolufy`)
- [ ] Import order: Standard library → Third party → Local (isort)
- [ ] Multi-line imports: Trailing comma, parentheses
- [ ] Must pass `pdm format` and `pdm lint` (Black, Ruff)

## Documentation
- [ ] Module-level docstring at top of file
- [ ] Class docstrings: Purpose and usage
- [ ] Method docstrings: Args, Returns, Raises (when public)
- [ ] Complex logic: Inline comments explaining "why"
- [ ] No redundant comments (code should be self-documenting)

## Naming Conventions
- [ ] Classes: `PascalCase` (e.g., `ConbusService`, `EventTelegram`)
- [ ] Functions/methods: `snake_case` (e.g., `send_telegram`, `get_config`)
- [ ] Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_TIMEOUT`)
- [ ] Private methods: `_leading_underscore` (e.g., `_parse_telegrams`)
- [ ] Type variables: `T`, `K`, `V` (single uppercase letter)

## Error Handling
- [ ] Use specific exceptions (not bare `Exception`)
- [ ] Custom exceptions inherit from base project exception
- [ ] Log errors with context: `self.logger.error(f"Failed: {e}")`
- [ ] Clean up resources in `finally` blocks
- [ ] Return `Response` objects with `success`, `data`, `error` fields

## Services
- [ ] Constructor: Accept dependencies via DI (no instantiation)
- [ ] Logger: `self.logger = logging.getLogger(__name__)`
- [ ] Context manager support: Implement `__enter__` and `__exit__` when managing resources
- [ ] No direct socket/connection creation (use ConnectionPool)
- [ ] Methods return typed responses (Pydantic models or `Response`)

## Models (Pydantic)
- [ ] Use `@dataclass` decorator when needed (Event models)
- [ ] Default values where appropriate
- [ ] `__post_init__` for computed fields (dataclasses)
- [ ] `@property` for derived attributes
- [ ] `to_dict()` method for JSON serialization
- [ ] `__str__` method for human-readable representation

## CLI Commands
- [ ] Use `@click.command()` or `@click.group()`
- [ ] Docstring becomes help text
- [ ] Help colors: `cls=HelpColorsGroup`
- [ ] Resolve services from context: `ctx.obj["container"].container.resolve(Service)`
- [ ] NO business logic in commands (delegate to services)
- [ ] Return type: `None` (Click handles output)

## Testing
- [ ] Test file naming: `test_*.py` or `*_test.py`
- [ ] Test class naming: `Test*` (e.g., `TestConbusService`)
- [ ] Test function naming: `test_*` (e.g., `test_send_telegram`)
- [ ] Mock external dependencies (socket, files, etc.)
- [ ] Use fixtures for common setup
- [ ] Minimum 75% coverage
- [ ] Run `pdm test-quick` before commit

## Dependencies
- [ ] Never instantiate services directly (use ServiceContainer)
- [ ] Inject dependencies via constructor
- [ ] Register services in `ServiceContainer._register_services()`
- [ ] Use EventBus for async/cross-service communication
- [ ] Singleton scope for stateful services

## Logging
- [ ] Use `self.logger` (initialized in `__init__`)
- [ ] Levels: DEBUG (verbose), INFO (key operations), ERROR (failures)
- [ ] Format: `f-string` with context
- [ ] No sensitive data (serial numbers, credentials)
- [ ] Log before/after critical operations

## Dead Code
- [ ] No commented-out code (remove or explain why)
- [ ] No unused imports (isort + ruff will catch)
- [ ] No unused variables (mypy will catch)
- [ ] Must pass `pdm vulture` (dead code detector)
- [ ] Must pass `pdm refurb` (modernization checker)

## Pre-Commit Checklist
Run before committing:
```bash
pdm check  # Runs all quality checks
```

Or individually:
```bash
pdm clean       # Remove coverage/cache
pdm lint        # Ruff linting
pdm format      # Black formatting
pdm typecheck   # Mypy type checking
pdm vulture     # Dead code detection
pdm refurb      # Modernization
pdm isort       # Import sorting
pdm absolufy    # Absolute imports
pdm test-quick  # Fast tests
pdm test-cov    # Full coverage
```
