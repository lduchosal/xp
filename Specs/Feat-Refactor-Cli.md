# CLI Refactoring Specification

## Problem Statement

The `src/xp/cli/main.py` file has grown to **2,128 lines** of code, making it difficult to maintain, test, and extend. This monolithic structure violates the Single Responsibility Principle and creates several maintenance issues.

## Current Issues

### 1. Monolithic Architecture
- All CLI commands (6 groups, 25+ subcommands) defined in single file
- Mixed concerns: command definition, business logic, formatting, error handling
- Difficult to locate and modify specific commands

### 2. Code Duplication
- Identical JSON/text output patterns repeated ~25 times
- Same error handling structure across all commands
- Repeated service instantiation and configuration

### 3. Poor Testability
- Commands tightly coupled with Click framework
- Business logic mixed with presentation logic
- Difficult to unit test individual commands

### 4. Maintenance Burden
- Large file difficult to navigate (2,128 lines)
- Changes to common patterns require updates across multiple locations
- High risk of merge conflicts in team development

## Proposed Refactoring Strategy

### Phase 1: Extract Command Groups (Priority: High)

Split main.py into separate command modules:

```
src/xp/cli/
├── main.py                 # Entry point + root CLI (100 lines)
├── commands/
│   ├── __init__.py
│   ├── telegram_commands.py    # ~400 lines → 200 lines
│   ├── module_commands.py      # ~200 lines → 100 lines
│   ├── checksum_commands.py    # ~150 lines → 75 lines
│   ├── linknumber_commands.py  # ~200 lines → 100 lines
│   ├── version_commands.py     # ~150 lines → 75 lines
│   ├── discovery_commands.py   # ~350 lines → 175 lines
│   ├── file_commands.py        # ~400 lines → 200 lines
│   ├── server_commands.py      # ~200 lines → 100 lines
│   └── conbus_commands.py      # ~400 lines → 200 lines
└── utils/
    ├── __init__.py
    ├── decorators.py           # Common decorators
    ├── formatters.py           # Output formatting
    └── error_handlers.py       # Error handling
```

### Phase 2: Create Shared Utilities (Priority: High)

#### A. Output Formatter Utility
```python
# src/xp/cli/utils/formatters.py
class OutputFormatter:
    def __init__(self, json_output: bool = False):
        self.json_output = json_output
    
    def success_response(self, data: dict) -> str:
        if self.json_output:
            return json.dumps(data, indent=2)
        return self._format_text(data)
    
    def error_response(self, error: str, extra_data: dict = None) -> str:
        # Standardized error formatting
```

#### B. Command Decorators
```python
# src/xp/cli/utils/decorators.py
def handle_service_errors(service_exceptions: tuple):
    """Decorator to handle common service exceptions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except service_exceptions as e:
                # Standardized error handling
        return wrapper
    return decorator

def json_output_option(func):
    """Decorator to add --json-output option"""
    return click.option('--json-output', '-j', is_flag=True, 
                       help='Output in JSON format')(func)
```

### Phase 3: Abstract Command Patterns (Priority: Medium)

#### A. Base Command Classes
```python
# src/xp/cli/commands/base.py
class BaseCommand:
    def __init__(self, json_output: bool = False):
        self.formatter = OutputFormatter(json_output)
    
    def handle_service_error(self, error: Exception, context: dict):
        """Standardized service error handling"""
    
    def execute_with_service(self, service_class, operation, *args, **kwargs):
        """Template method for service operations"""
```

#### B. Command Templates
```python
class ParseCommand(BaseCommand):
    """Template for parse-style commands"""
    def execute(self, input_data: str, validate_checksum: bool = False):
        # Template implementation

class GenerateCommand(BaseCommand):
    """Template for generate-style commands"""
    def execute(self, **params):
        # Template implementation
```

### Phase 4: Improve Command Structure (Priority: Medium)

#### A. Consistent Command Interface
- All commands use same option patterns
- Consistent parameter validation
- Standardized help text format

#### B. Enhanced Error Handling
```python
# src/xp/cli/utils/error_handlers.py
class CLIErrorHandler:
    @staticmethod
    def handle_parsing_error(error, json_output, raw_input):
        """Handle telegram parsing errors"""
    
    @staticmethod
    def handle_connection_error(error, json_output, config):
        """Handle connection/network errors"""
```

### Phase 5: Add Command Testing Framework (Priority: Low)

```python
# tests/unit/test_commands/
class TestTelegramCommands:
    def test_parse_event_command_success(self):
        # Test with mock service
    
    def test_parse_event_command_json_output(self):
        # Test JSON formatting
```

## Implementation Plan

### Week 1: Foundation
- [ ] Create new directory structure
- [ ] Implement OutputFormatter utility
- [ ] Create common decorators
- [ ] Extract telegram_commands.py (largest group)

### Week 2: Core Commands
- [ ] Extract module_commands.py
- [ ] Extract checksum_commands.py  
- [ ] Extract linknumber_commands.py
- [ ] Implement error handlers utility

### Week 3: Complex Commands
- [ ] Extract discovery_commands.py (complex parsing logic)
- [ ] Extract file_commands.py (multiple helper functions)
- [ ] Create base command classes

### Week 4: Service Commands
- [ ] Extract server_commands.py
- [ ] Extract conbus_commands.py
- [ ] Extract version_commands.py
- [ ] Refactor main.py to import command groups

### Week 5: Polish & Testing
- [ ] Add command templates
- [ ] Implement comprehensive testing
- [ ] Documentation updates
- [ ] Performance validation

## Expected Benefits

### Maintainability
- **80% reduction** in file size (2,128 → ~400 lines for main.py)
- Individual command groups easily discoverable and editable
- Consistent patterns across all commands

### Testability  
- Commands can be unit tested independently
- Service layer properly mocked
- Output formatting tested separately

### Extensibility
- New commands follow established patterns
- Common functionality reused via utilities
- Easy to add new command groups

### Code Quality
- **~50% reduction** in code duplication
- Separation of concerns enforced
- Single Responsibility Principle followed

## Risk Mitigation

1. **Breaking Changes**: Maintain backward compatibility by preserving all command interfaces
2. **Testing**: Implement comprehensive test suite during refactoring
3. **Rollback Plan**: Keep original main.py as backup during transition
4. **Gradual Migration**: Move one command group at a time, validating functionality

## Success Metrics

- [ ] Main.py reduced from 2,128 to under 500 lines
- [ ] Zero functional regressions in CLI behavior  
- [ ] Command response time unchanged
- [ ] Test coverage increased to >90% for CLI commands
- [ ] Developer productivity improved (faster feature additions)