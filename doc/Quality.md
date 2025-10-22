# Quality Management

## Quick Checks (Development)
- `pdm run typecheck` - Mypy type checking
- `pdm run flake8` - Flake8 code quality, and doc checker
- `pdm run interrogate` - doc checker
- `pdm run refurb` - Refurbishing code
- `pdm test-quick` - Fast test validation
- `pdm lint` - Ruff linting
- `pdm format` - Black formatting

## Full Quality Check
```bash
pdm check  # Runs: lint, format, typecheck, refurb, test
```

## Final Validation
```bash
sh publish.sh --quality
```

## Requirements
- **Test Coverage**: Minimum 75% (`pdm test-cov`)
- **Type Safety**: Strict mypy (no untyped defs)
- **Python Versions**: 3.11, 3.12, 3.13
- **Line Length**: 88 characters
- **Import Style**: Absolute imports (`pdm absolufy`)