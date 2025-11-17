# Quality Management

Run checklist and fix issues until all quality check has succeed

## Quality checklist
-[ ] `pdm run typecheck` - Mypy type checking
-[ ] `pdm run flake8` - Flake8 code quality, and doc checker
-[ ] `pdm run interrogate` - doc checker
-[ ] `pdm run refurb` - Refurbishing code
-[ ] `pdm test-quick` - Fast test validation
-[ ] `pdm absolufy` - Absolute imports
-[ ] `pdm lint` - Ruff linting
-[ ] `pdm format` - Black formatting
-[ ] `pdm check` - Quality check
-[ ] `sh publish.sh --quality` - Ultimate quality check

## Requirements
- **Test Coverage**: Minimum 75% (`pdm test-cov`)
- **Type Safety**: Strict mypy (no untyped defs)
- **Python Versions**: 3.11, 3.12, 3.13
- **Line Length**: 88 characters
