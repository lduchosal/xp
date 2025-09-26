# Dead Code Cleanup Specification

## Overview

Analysis of the XP Protocol Communication Tool codebase identified several areas of dead, unused, and potentially unreachable code that require cleanup.

**Project Stats:**
- 2,626 total Python files (including build artifacts)
- ~11,871 lines of code in src/
- 663 import statements across 122 files
- 210 function/class definitions across 110 files

## Identified Issues

### 1. Unused Imports
**Location:** `src/xp/api/routers/__init__.py:2`
```python
from .conbus import router  # F401: imported but unused
```

### 2. Exception Handler Variables
Multiple files contain unused exception variables in `except` blocks:
- `src/xp/services/conbus_blink_service.py:43` - exc_tb, exc_type, exc_val
- `src/xp/services/conbus_connection_pool.py:146` - exc_tb, exc_type, exc_val
- `src/xp/services/conbus_custom_service.py:67` - exc_tb, exc_type, exc_val
- `src/xp/services/conbus_datapoint_service.py:122` - exc_tb, exc_type, exc_val
- `src/xp/services/conbus_discover_service.py:82` - exc_tb, exc_type, exc_val
- `src/xp/services/conbus_linknumber_service.py:44-46` - exc_type, exc_val, exc_tb
- And 9 more similar instances across services

### 3. Unused Event Handler Parameters
**Location:** `src/xp/services/homekit_module_service.py`
- Line 53, 61, 68, 101: `sender` parameter unused in event handlers

### 4. Build Artifacts
The `build/` directory contains 51 duplicate Python files that should be excluded from analysis.

## Recommended Tools

### Static Analysis Tools

1. **Ruff** (Already configured in pyproject.toml)
   ```bash
   ruff check --select F401,F841 src/  # Find unused imports/variables
   ```

2. **Vulture** (Already in dev dependencies)
   ```bash
   vulture src/ --min-confidence 80
   ```

3. **MyPy** (Already configured)
   ```bash
   mypy src/ --warn-unreachable
   ```

4. **Coverage.py** (Already configured)
   ```bash
   pytest --cov=src/xp --cov-report=term-missing --cov-fail-under=60
   pdm run test-ci  # Generates coverage.xml for dead code analysis
   ```

### Additional Recommended Tools

5. **Dead** - Advanced dead code elimination
   ```bash
   pip install dead
   dead --exclude tests/ src/
   ```

6. **Unimport** - Import optimization
   ```bash
   pip install unimport
   unimport --check src/
   ```

7. **Refurb** - Python refactoring suggestions
   ```bash
   pip install refurb
   refurb src/
   ```

8. **Bandit** - Security linting for unused credentials/keys
   ```bash
   pip install bandit
   bandit -r src/
   ```

9. **Coverage-based Dead Code Analysis** - Use coverage.xml to identify untested code
   ```bash
   # Generate coverage.xml
   pdm run test-ci

   # Analyze uncovered lines as potential dead code
   python -c "
   import xml.etree.ElementTree as ET
   tree = ET.parse('coverage.xml')
   for cls in tree.findall('.//class'):
       filename = cls.get('filename')
       lines = cls.find('lines')
       uncovered = [line.get('number') for line in lines.findall('line') if line.get('hits') == '0']
       if uncovered:
           print(f'{filename}: Lines {uncovered} never executed')
   "
   ```

## Cleanup Checklist

### Phase 1: Safe Removals
- [ ] Remove unused import in `src/xp/api/routers/__init__.py`
- [ ] Fix or suppress unused exception variables (32+ instances)
- [ ] Remove unused `sender` parameters in HomeKit event handlers
- [ ] Clean build artifacts from version control

### Phase 2: Deep Analysis
- [ ] Generate and analyze coverage.xml to identify untested code paths
- [ ] Run vulture with lower confidence threshold (60%) to find more candidates
- [ ] Review CLI command registration for unused commands
- [ ] Audit API endpoints for unused routes
- [ ] Check model classes for unused methods/properties
- [ ] Cross-reference coverage gaps with static analysis results

### Phase 3: Refactoring
- [ ] Consolidate duplicate exception handling patterns
- [ ] Extract common validation logic
- [ ] Remove debug/development-only code paths
- [ ] Simplify overly complex conditional logic

### Phase 4: Documentation
- [ ] Update API documentation after route cleanup
- [ ] Remove outdated code examples
- [ ] Document intentionally unused code (e.g., event handlers)

## Quality Section

### Code Quality Metrics
- **Current test coverage:** 60% minimum (per pyproject.toml)
- **Type checking:** Enabled with mypy strict mode
- **Linting:** Ruff + Black formatting
- **Lines of code:** 11,871 (target: reduce by 5-10%)

### Quality Standards
1. All unused imports must be removed
2. Exception handlers should use `_` for unused variables
3. Event handlers with unused parameters should be documented
4. No dead code paths should remain after cleanup
5. Test coverage should not decrease during cleanup

### Pre-commit Hooks
Recommend adding these tools to pre-commit configuration:
```yaml
repos:
  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.10
    hooks:
      - id: vulture
  - repo: https://github.com/hakancelik96/unimport
    rev: 0.16.0
    hooks:
      - id: unimport
```

## Test Section

### Test Coverage Analysis
Current coverage excludes:
- `tests/*`
- `src/xp/__main__.py`
- Abstract methods
- Debug code
- Exception handlers with `pragma: no cover`

### Test Strategy for Cleanup

1. **Before Cleanup**
   ```bash
   # Establish baseline coverage
   pdm run test-cov
   # Record current test results
   pdm run test > baseline_results.txt
   ```

2. **During Cleanup**
   ```bash
   # Run after each cleanup phase
   pdm run test-quick  # Fast validation
   pdm run lint       # Code quality check
   ```

3. **After Cleanup**
   ```bash
   # Full test suite with coverage
   pdm run test
   # Ensure no regressions
   diff baseline_results.txt new_results.txt
   ```

### Integration Testing
- [ ] API endpoints still function after route cleanup
- [ ] CLI commands work after command cleanup
- [ ] HomeKit integration remains stable
- [ ] Telegram parsing accuracy unchanged
- [ ] Server emulation features intact

### Regression Prevention
- Add tests for previously uncovered code before removing
- Use feature flags to disable rather than delete uncertain code
- Maintain git history for easy rollback
- Document reasons for removal in commit messages

## Implementation Timeline
- **Phase 1:** 2 hours (safe removals)
- **Phase 2:** 4 hours (deep analysis)
- **Phase 3:** 6 hours (refactoring)
- **Phase 4:** 2 hours (documentation)
- **Total:** 14 hours estimated

## Success Criteria
- [ ] Zero unused import warnings from Ruff
- [ ] Vulture confidence >95% on remaining code
- [ ] No decrease in test coverage percentage
- [ ] All CI/CD pipeline checks pass
- [ ] Code complexity metrics improved
- [ ] Documentation updated and accurate