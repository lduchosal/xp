# Quality Management

Run checklist and fix issues until all quality check has succeed

## Quality checklist
-[ ] `pdm run lint` - Ruff linting (`select = ["ALL"]` + preview rules), auto-fix
-[ ] `pdm run format` - Ruff formatting (imports, docstrings code, style)
-[ ] `pdm run typecheck` - Mypy strict type checking (src and tests, py.typed)
-[ ] `pdm run vulture` - Dead code detection
-[ ] `pdm run quality` - All static gates, check-only (same as CI)
-[ ] `pdm run test-quick` - Fast test validation
-[ ] `pdm run check` - Full quality check
-[ ] `sh publish.sh --quality` - Ultimate quality check

## Principles
- Fix the code, never relax the rule. `noqa` only for external framework
  constraints (Twisted method names, pytest bare asserts, positional
  framework callbacks), always with a justification comment on the line.
- Ruff replaces black, flake8, isort, docformatter, interrogate, refurb
  and absolufy-imports. `select = ["ALL"]` grows automatically with every
  ruff release; preview rules are opted in explicitly in pyproject.toml.
- Tool versions have no upper bound: new checks from tool updates are
  new findings to fix, never regressions to avoid.

## Requirements
- **Test Coverage**: Minimum 75% (`pdm test-cov`)
- **Type Safety**: Strict mypy (no untyped defs, tests included)
- **Datetimes**: Always timezone-aware (`xp.utils.time_utils.local_now`)
- **Python Versions**: 3.11, 3.12, 3.13
- **Line Length**: 88 characters
