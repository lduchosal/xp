# Quality Management

## Quick Checks (Development)
- `pdm test-quick` - Fast test validation
- `pdm lint` - Ruff linting
- `pdm format` - Black formatting
- `pdm typecheck` - Mypy type checking

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