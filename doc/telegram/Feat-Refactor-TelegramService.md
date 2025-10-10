  # TelegramService Refactoring Specification

## Overview

The current `TelegramService` class (373 lines) handles parsing of multiple telegram types (Event, System, Reply) in a single monolithic service. This refactoring will split it into specialized parsers following the Single Responsibility Principle and improve maintainability.

## Current Architecture Analysis

### TelegramService (src/xp/services/telegram_service.py)
- **Size**: 373 lines
- **Responsibilities**:
  - Event telegram parsing (`<E|O>` format)
  - System telegram parsing (`<S>` format)
  - Reply telegram parsing (`<R>` format)
  - Checksum validation (static method)
  - Formatting utilities (static methods)
  - Auto-detection and routing

### Key Dependencies
- **Models**: EventTelegram, SystemTelegram, ReplyTelegram, OutputTelegram
- **Utils**: checksum.calculate_checksum
- **Enums**: EventType, DataPointType, SystemFunction

### Integration Points (11 services + CLI)
- `server_service.py` - Uses parse_event_telegram()
- `conbus_*_service.py` (6 files) - Various telegram parsing
- `log_file_service.py` - File parsing with telegram detection
- `telegram_output_service.py` - Telegram processing
- CLI commands (`telegram_parse_commands.py`) - parse/validate commands
- Test suite (22 test files)

## Proposed Refactored Architecture

### Core Parser Classes

#### 1. BaseTelegramParser (Abstract)
```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T', bound=Telegram)

class BaseTelegramParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, raw_telegram: str) -> T:
        pass

    @abstractmethod
    def validate_format(self, raw_telegram: str) -> bool:
        pass

    def validate_checksum(self, telegram: T) -> bool:
        # Shared checksum validation logic
```

#### 2. EventTelegramParser
```python
class EventTelegramParser(BaseTelegramParser[EventTelegram]):
    PATTERN = re.compile(r"^<([EO])(\d{1,2})L(\d{2})I(\d{2})([MB])([A-Z0-9]{2})>$")

    def parse(self, raw_telegram: str) -> EventTelegram:
        # Current parse_event_telegram logic

    def format_summary(self, telegram: EventTelegram) -> str:
        # Current format_event_telegram_summary logic
```

#### 3. SystemTelegramParser
```python
class SystemTelegramParser(BaseTelegramParser[SystemTelegram]):
    PATTERN = re.compile(r"^<S(\d{10})F(\d{2})D(\d{2})(.*?)([A-Z0-9]{2})>$")

    def parse(self, raw_telegram: str) -> SystemTelegram:
        # Current parse_system_telegram logic

    def format_summary(self, telegram: SystemTelegram) -> str:
        # Current format_system_telegram_summary logic
```

#### 4. ReplyTelegramParser
```python
class ReplyTelegramParser(BaseTelegramParser[ReplyTelegram]):
    PATTERN = re.compile(r"^<R(\d{10})F(\d{2})(.+?)([A-Z0-9]{2})>$")

    def parse(self, raw_telegram: str) -> ReplyTelegram:
        # Current parse_reply_telegram logic

    def format_summary(self, telegram: ReplyTelegram) -> str:
        # Current format_reply_telegram_summary logic
```

### Orchestrator Service

#### TelegramParserFactory
```python
class TelegramParserFactory:
    def __init__(self):
        self._parsers = {
            'E': EventTelegramParser(),
            'O': EventTelegramParser(),  # Output telegrams use same parser
            'S': SystemTelegramParser(),
            'R': ReplyTelegramParser(),
        }

    def get_parser(self, telegram_type: str) -> BaseTelegramParser:
        return self._parsers.get(telegram_type)

    def detect_type(self, raw_telegram: str) -> str:
        # Auto-detection logic

    def parse_any(self, raw_telegram: str) -> Union[EventTelegram, SystemTelegram, ReplyTelegram]:
        # Current parse_telegram logic using factory
```

#### Refactored TelegramService
```python
class TelegramService:
    def __init__(self):
        self.factory = TelegramParserFactory()

    def parse_telegram(self, raw_telegram: str) -> Union[EventTelegram, SystemTelegram, ReplyTelegram]:
        return self.factory.parse_any(raw_telegram)

    def parse_event_telegram(self, raw_telegram: str) -> EventTelegram:
        return self.factory.get_parser('E').parse(raw_telegram)

    def parse_system_telegram(self, raw_telegram: str) -> SystemTelegram:
        return self.factory.get_parser('S').parse(raw_telegram)

    def parse_reply_telegram(self, raw_telegram: str) -> ReplyTelegram:
        return self.factory.get_parser('R').parse(raw_telegram)

    @staticmethod
    def validate_checksum(telegram: Union[EventTelegram, ReplyTelegram, SystemTelegram]) -> bool:
        # Keep as static for backward compatibility
```

## Refactoring Checklist

### Phase 1: Create Base Classes
- [ ] Create `base_telegram_parser.py` with abstract BaseTelegramParser
- [ ] Move shared checksum validation to base class
- [ ] Add type safety with Generic[T] support

### Phase 2: Extract Specialized Parsers
- [ ] Create `event_telegram_parser.py`
  - [ ] Move EVENT_TELEGRAM_PATTERN
  - [ ] Move parse_event_telegram logic
  - [ ] Move format_event_telegram_summary logic
  - [ ] Add unit tests
- [ ] Create `system_telegram_parser.py`
  - [ ] Move SYSTEM_TELEGRAM_PATTERN
  - [ ] Move parse_system_telegram logic
  - [ ] Move format_system_telegram_summary logic
  - [ ] Add unit tests
- [ ] Create `reply_telegram_parser.py`
  - [ ] Move REPLY_TELEGRAM_PATTERN
  - [ ] Move parse_reply_telegram logic
  - [ ] Move format_reply_telegram_summary logic
  - [ ] Add unit tests

### Phase 3: Create Factory
- [ ] Create `telegram_parser_factory.py`
  - [ ] Implement parser registration
  - [ ] Move auto-detection logic
  - [ ] Add parse_any method
  - [ ] Add unit tests

### Phase 4: Refactor TelegramService
- [ ] Update TelegramService to use factory pattern
- [ ] Maintain backward compatibility for public API
- [ ] Keep static methods for compatibility
- [ ] Update imports and dependencies

### Phase 5: Update Integration Points
- [ ] Update services (11 files):
  - [ ] `server_service.py`
  - [ ] `conbus_*_service.py` (6 files)
  - [ ] `log_file_service.py`
  - [ ] `telegram_output_service.py`
- [ ] Update CLI commands
- [ ] Update service exports in `__init__.py`

### Phase 6: Testing & Validation
- [ ] Run existing test suite (22 test files)
- [ ] Add new unit tests for parsers
- [ ] Add integration tests for factory
- [ ] Performance testing (ensure no regression)
- [ ] Update test imports

### Phase 7: Documentation
- [ ] Update docstrings for new classes
- [ ] Update type hints throughout
- [ ] Add usage examples
- [ ] Update any relevant documentation files

## Benefits

### Maintainability
- **Single Responsibility**: Each parser handles one telegram type
- **Reduced Complexity**: 373-line class split into focused 80-100 line classes
- **Easier Testing**: Isolated parser logic with dedicated test suites

### Extensibility
- **New Telegram Types**: Easy to add via factory registration
- **Parser Customization**: Override specific methods without affecting others
- **Type Safety**: Generic base class ensures proper typing

### Performance
- **Lazy Loading**: Parsers created only when needed
- **Pattern Caching**: Regex patterns compiled once per parser
- **Reduced Parsing Overhead**: Direct parser access without type detection

## Backward Compatibility

- All public methods of TelegramService remain unchanged
- Import paths stay the same (`from xp.services.telegram.telegram_service import TelegramService`)
- Static methods preserved for existing code
- Exception types and error messages unchanged

## Risk Assessment

### Low Risk
- Extensive test coverage (22 test files) provides safety net
- Incremental refactoring allows rollback at any phase
- Backward compatibility ensures no breaking changes

### Mitigation Strategies
- Keep original TelegramService until all integration points updated
- Run full test suite after each phase
- Performance benchmarking to detect regressions
