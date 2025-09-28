# Feature Specification: Telegram Type

## Overview

This feature adds a standardized `telegram_type` property to the base `Telegram` model to provide consistent type identification across all telegram variants.

## Motivation

Currently, different telegram types (Event, Reply, System) are handled separately, but there's no unified way to identify the telegram type at the base level. This creates inconsistencies:

- `ReplyTelegram.to_dict()` returns `"telegram_type": "reply"` (hardcoded)
- `SystemTelegram.to_dict()` returns `"telegram_type": "system"` (hardcoded)
- `EventTelegram.to_dict()` doesn't include any telegram_type field

This feature standardizes telegram type identification across the codebase.

## Specification

### TelegramType Enum

Create a new enum `TelegramType` with the following values:

```python
from enum import Enum

class TelegramType(Enum):
    EVENT = "event"
    REPLY = "reply"
    SYSTEM = "system"
```

### Base Telegram Model Changes

Add a `telegram_type` property to the base `Telegram` class:

```python
@dataclass
class Telegram:
    checksum: str
    raw_telegram: str
    checksum_validated: Optional[bool] = None
    timestamp: Optional[datetime] = None
    telegram_type: TelegramType = TelegramType.EVENT  # Default to EVENT
```

### Subclass Implementation

Each telegram subclass should set the appropriate type:

- `EventTelegram`: `telegram_type = TelegramType.EVENT`
- `ReplyTelegram`: `telegram_type = TelegramType.REPLY`
- `SystemTelegram`: `telegram_type = TelegramType.SYSTEM`

### Service Modifications

Services that handle telegrams should be updated to:

1. Use the `telegram_type` property for type checking instead of `isinstance()` where appropriate
2. Ensure consistent serialization using the enum values
3. Update any filtering or routing logic to leverage the standardized type

## Implementation Details

### File Changes Required

1. **`src/xp/models/telegram_type.py`** (new file)
   - Define the `TelegramType` enum

2. **`src/xp/models/telegram.py`**
   - Import `TelegramType`
   - Add `telegram_type: TelegramType` property with default value

3. **`src/xp/models/event_telegram.py`**
   - Set `telegram_type = TelegramType.EVENT` in `__post_init__`
   - Update `to_dict()` to use the enum value

4. **`src/xp/models/reply_telegram.py`**
   - Set `telegram_type = TelegramType.REPLY` in `__post_init__`
   - Remove hardcoded `"telegram_type": "reply"` from `to_dict()` and use enum value

5. **`src/xp/models/system_telegram.py`**
   - Set `telegram_type = TelegramType.SYSTEM` in `__post_init__`
   - Remove hardcoded `"telegram_type": "system"` from `to_dict()` and use enum value

6. **Service files**
   - Update telegram services to use the new `telegram_type` property where applicable

## Benefits

1. **Consistency**: All telegram types have a standardized way to identify their type
2. **Type Safety**: Using an enum prevents typos and provides IDE support
3. **Maintainability**: Centralized type definitions make changes easier
4. **API Consistency**: All telegram serializations will include the same telegram_type field format

## Backward Compatibility

This change maintains backward compatibility:
- Existing JSON serialization will continue to work (same string values)
- Existing code using `isinstance()` checks will continue to work
- New code can use the cleaner `telegram.telegram_type == TelegramType.EVENT` syntax

## Testing

- Unit tests should verify that each telegram type sets the correct `telegram_type` value
- Integration tests should verify that JSON serialization includes the correct telegram_type
- Tests should verify that existing functionality continues to work unchanged