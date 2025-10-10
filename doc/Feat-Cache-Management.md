# Feature Specification: Event-Based Cache Management

## Overview

Implement cache invalidation and update mechanisms triggered by Event Telegrams received from the CONSON XP Protocol. When devices report state changes via event telegrams, the cache should be updated to reflect the new state without requiring explicit queries.

## Problem Statement

Currently, the cache system (implemented in `HomeKitCacheService`) stores datapoint responses but does not update when physical state changes occur:

- User presses a button on XP24 module → Event telegram `<E12L01I08MAK>` received
- Module changes output state (e.g., light turns ON)
- Cache still contains old state (e.g., OFF)
- HomeKit queries cached value and shows incorrect state
- User must wait for cache miss or manual refresh to see correct state

**This creates a stale cache problem where physical actions are not reflected in the cached state.**

## Current System Architecture

### Event Flow

1. **Physical Action**: User presses button on module (e.g., XP24 with `module_type_code=12`, `link_number=01`)
2. **Event Telegram**: Module sends `<E12L01I08MAK>` via TCP
3. **Protocol Layer**: `TelegramProtocol` receives telegram and dispatches `TelegramReceivedEvent`
4. **Service Layer**: `HomeKitService.handle_telegram_received()` forwards Event telegrams (type="E") as `EventTelegramReceivedEvent`
5. **Current Behavior**: Event is logged but cache is NOT updated

### Event Telegram Format

```
<E{module_type_code}L{link_number}I{input_number}{event_type}{checksum}>

Example: <E12L01I83MAK>
- E: Event telegram type
- 12: module_type_code (XP24 module)
- L01: link_number (link 01)
- I83: input_number (input 3)
- M: event_type (Button press - M=press, B=release)
- AK: checksum
```

**Event Type Mapping:**
- `M` = Button Press (EventType.BUTTON_PRESS)
- `B` = Button Release (EventType.BUTTON_RELEASE)


**Input Number Mapping:**
- `80` = input_number 0
- `81` = input_number 1
- `82` = input_number 2
- `83` = input_number 3

### ConsonModuleConfig Mapping

The `conson.yml` configuration provides the mapping from `(module_type_code, link_number)` to `serial_number`:

```yaml
- name: A4
  serial_number: "0020044991"
  module_type: XP24
  module_type_code: 07
  link_number: 02
  module_number: 2
```

**Key relationships:**
- `module_type_code` + `link_number` → identifies a specific module in the bus
- `serial_number` → unique identifier for protocol queries
- Each module can have multiple inputs (I00-I09 for buttons)
- Each module can have multiple outputs (controlled by inputs via action tables)
- HomekitModuleService provide finders and lookup

### Current Cache Structure

From `HomeKitCacheService` (src/xp/services/homekit/homekit_cache_service.py:38):

```python
cache: dict[tuple[str, DataPointType], CacheEntry] = {}

# Cache key: (serial_number, datapoint_type)
# Example: ("0020044991", DataPointType.OUTPUT_STATE)

CacheEntry = {
    "event": OutputStateReceivedEvent | LightLevelReceivedEvent,
    "timestamp": datetime
}
```

## Proposed Solution

### Strategy 1: Cache Invalidation (Recommended for Phase 1)

When an Event Telegram is received, **invalidate** (flush) the cache entries for the affected module to force fresh queries.

#### Advantages
- Simple and safe
- Guarantees fresh data after state changes
- No risk of incorrect state assumptions
- Works even if action tables are complex or unknown

#### Implementation Flow

1. **Event Reception**: `EventTelegramReceivedEvent` dispatched with telegram payload `E12L01I80MAK`
2. **Parse Event**: Extract `module_type_code=12`, `link_number=0`
3. **Lookup Serial**: Use `ConsonModuleListConfig` to find `serial_number` from `(module_type_code, link_number)`
4. **Invalidate Cache**: Remove all cache entries with matching `serial_number`:
   - `(serial_number, DataPointType.OUTPUT_STATE)`
   - `(serial_number, DataPointType.LIGHT_LEVEL)`
5. **Next Query**: Cache miss triggers fresh protocol query, cache is populated with correct state

#### Code Example

```python
class HomeKitCacheService:
    def __init__(self, event_bus: EventBus, conson_config: ConsonModuleListConfig):
        self.event_bus = event_bus
        self.conson_config = conson_config
        self.cache: dict[tuple[str, DataPointType], CacheEntry] = {}

        # Register new handler
        self.event_bus.on(EventTelegramReceivedEvent, self.handle_event_telegram)

    def handle_event_telegram(self, event: EventTelegramReceivedEvent) -> None:
        """Invalidate cache when event telegram received."""
        # Parse event telegram to extract module_type_code and link_number
        event_telegram = self.telegram_service.parse_event_telegram(event.frame)

        # Find module in conson config
        module = self._find_module(
            event_telegram.module_type,
            event_telegram.link_number
        )

        if not module:
            self.logger.warning(
                f"Module not found in config: "
                f"type={event_telegram.module_type}, link={event_telegram.link_number}"
            )
            return

        # Invalidate all cache entries for this serial number
        self._invalidate_module_cache(module.serial_number)

    def _find_module(self, module_type_code: int, link_number: int) -> ConsonModuleConfig | None:
        """Find module by module_type_code and link_number."""
        for module in self.conson_config.root:
            if (module.module_type_code == module_type_code and
                module.link_number == link_number):
                return module
        return None

    def _invalidate_module_cache(self, serial_number: str) -> None:
        """Remove all cache entries for a given serial number."""
        keys_to_remove = [
            key for key in self.cache.keys()
            if key[0] == serial_number
        ]

        for key in keys_to_remove:
            del self.cache[key]
            self.logger.info(f"Invalidated cache: serial={key[0]}, type={key[1]}")
```

### Strategy 2: Smart Cache Update (Future Enhancement)

Instead of invalidating, **update** the cache with the new state inferred from the event.

#### Challenges
- Requires understanding module action tables (input → output mappings)
- Action tables are complex and module-specific
- Risk of incorrect assumptions leading to wrong cached state
- Event telegrams don't directly specify which output changed

#### When to Consider
- After action table parsing is implemented
- When event telegram → output state mapping is well-defined
- For performance optimization (avoid extra protocol queries)

## Implementation Plan

### Phase 1: Cache Invalidation

**Files to Modify:**

1. **`src/xp/services/homekit/homekit_cache_service.py`**
   - Add `conson_config: ConsonModuleListConfig` dependency
   - Add `telegram_service: TelegramService` dependency
   - Register handler for `EventTelegramReceivedEvent`
   - Implement `handle_event_telegram()`
   - Implement `_find_module(module_type_code, link_number)`
   - Implement `_invalidate_module_cache(serial_number)`

2. **`src/xp/utils/dependencies.py`**
   - Inject `ConsonModuleListConfig` into `HomeKitCacheService`
   - Inject `TelegramService` into `HomeKitCacheService`

3. **`tests/unit/test_services/test_homekit_cache_service.py`**
   - Test `handle_event_telegram()` with valid module
   - Test `handle_event_telegram()` with unknown module
   - Test `_find_module()` with matching config
   - Test `_find_module()` with no match
   - Test `_invalidate_module_cache()` removes correct entries
   - Test cache invalidation doesn't affect other modules

### Dependencies

**Required Services:**
- `TelegramService` (for parsing event telegrams)
- `ConsonModuleListConfig` (for module_type_code/link_number → serial_number mapping)

**Required Events:**
- `EventTelegramReceivedEvent` (already exists, dispatched in `homekit_service.py:156`)

### Event Flow Diagram

```
[Physical Button Press]
         ↓
[XP Module generates Event: E12L01I08MAK]
         ↓
[TelegramProtocol receives via TCP]
         ↓
[TelegramReceivedEvent dispatched]
         ↓
[HomeKitService.handle_telegram_received()]
         ↓
[EventTelegramReceivedEvent dispatched]
         ↓
[HomeKitCacheService.handle_event_telegram()] ← NEW
         ↓
[Parse: module_type_code=12, link_number=01]
         ↓
[Lookup ConsonConfig → serial_number="0020044991"]
         ↓
[Invalidate cache entries for serial_number]
         ↓
[Next HomeKit query → Cache miss → Fresh protocol query]
```

## Testing Requirements

### Unit Tests

1. **Event Telegram Parsing Integration**
   - Test parsing `<E12L01I08MAK>` extracts correct `module_type_code` and `link_number`
   - Test both button press (M) and release (B) events

2. **Module Lookup**
   - Test `_find_module()` with exact match returns correct module
   - Test `_find_module()` with no match returns None
   - Test `_find_module()` handles multiple modules correctly

3. **Cache Invalidation**
   - Given: Cache contains `(serial_number, OUTPUT_STATE)` and `(serial_number, LIGHT_LEVEL)`
   - When: Event telegram received for that module
   - Then: Both entries are removed

4. **Cache Isolation**
   - Given: Cache contains entries for multiple modules
   - When: Event telegram received for one module
   - Then: Only that module's entries are removed

5. **Unknown Module Handling**
   - Given: Event telegram for module not in `conson.yml`
   - When: `handle_event_telegram()` called
   - Then: Warning logged, no cache changes, no exception

### Integration Tests

1. **End-to-End Cache Invalidation**
   - Setup: Populate cache with module state
   - Action: Dispatch `EventTelegramReceivedEvent`
   - Verify: Cache entry removed
   - Verify: Next query triggers protocol call

2. **Multi-Module Scenario**
   - Setup: Cache entries for modules A, B, C
   - Action: Event telegram for module B
   - Verify: Only module B cache cleared

## Configuration Changes

No changes required to configuration file formats. Existing `conson.yml` structure already provides necessary mappings.

## Performance Considerations

- **Cache Invalidation Overhead**: O(n) where n = cache size (acceptable for typical deployments)
- **Lookup Performance**: O(m) where m = number of modules in config (typically < 20 modules)
- **Protocol Query Impact**: Invalidation triggers one additional query per affected datapoint
- **Network Load**: Minimal - only queries when actual state changes occur

## Future Enhancements

1. **Selective Invalidation**
   - Parse action tables to determine which specific outputs changed
   - Only invalidate affected output cache entries

2. **Smart Cache Update**
   - Query module state immediately after event
   - Pre-populate cache with fresh data proactively

3. **Event Debouncing**
   - Multiple rapid button presses → single cache invalidation
   - Reduce protocol query storms

4. **Cache Statistics**
   - Track invalidation rate
   - Monitor cache hit/miss ratio after invalidations

5. **Action Table Integration**
   - Parse module action tables (stored in modules)
   - Map input events directly to output state changes
   - Update cache instead of invalidate

## References

- **Event Telegram Model**: `src/xp/models/telegram/event_telegram.py`
- **Telegram Protocol**: `src/xp/services/protocol/telegram_protocol.py:78` (Event telegram example)
- **HomeKit Service**: `src/xp/services/homekit/homekit_service.py:155-157` (Event forwarding)
- **Cache Service**: `src/xp/services/homekit/homekit_cache_service.py`
- **Conson Config**: `src/xp/models/homekit/homekit_conson_config.py`
- **Existing Cache Spec**: `doc/Feat-Bubus-Caching.md`
- **Protocol Events**: `src/xp/models/protocol/conbus_protocol.py:155-158`

## Success Criteria

- ✅ Event telegrams trigger cache invalidation for correct module
- ✅ Cache invalidation uses ConsonConfig mapping (module_type_code + link_number → serial_number)
- ✅ Only affected module's cache entries are removed
- ✅ Unknown modules are handled gracefully (logged, no crash)
- ✅ Unit test coverage ≥ 90% for new code
- ✅ Integration tests verify end-to-end flow
- ✅ No performance degradation (cache operations remain < 10ms)
