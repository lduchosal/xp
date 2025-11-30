# Quality Management

Run checklist and fix issues until all quality check has succeed

## Quality checklist
-[ ] `pdm run absolufy` - Absolute imports
-[ ] `pdm run isort` - Import sorting
-[ ] `pdm run format` - Black formatting
-[ ] `pdm run docformatter` - Docstring formatting (D205, D400, etc.)
-[ ] `pdm run typecheck` - Mypy type checking
-[ ] `pdm run flake8` - Flake8 code quality, and doc checker
-[ ] `pdm run interrogate` - Docstring coverage
-[ ] `pdm run refurb` - Refurbishing code
-[ ] `pdm run lint` - Ruff linting
-[ ] `pdm run vulture` - Dead code detection
-[ ] `pdm run test-quick` - Fast test validation
-[ ] `pdm run check` - Full quality check
-[ ] `sh publish.sh --quality` - Ultimate quality check

## Requirements
- **Test Coverage**: Minimum 75% (`pdm test-cov`)
- **Type Safety**: Strict mypy (no untyped defs)
- **Python Versions**: 3.11, 3.12, 3.13
- **Line Length**: 88 characters
