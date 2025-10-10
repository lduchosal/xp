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

### HAP Service-Driven Cache Refresh

When an Event Telegram is received, the `HomekitHapService` handles the event, looks up affected accessories using a dual-key registry structure, and requests cache refresh for them.

#### Dual-Key Registry Structure

The `HomekitHapService` maintains two registries for efficient bidirectional lookup:

```python
# Registry 1: Lookup by serial_number.output_number (existing - for state updates from protocol)
accessory_registry: Dict[str, Union[LightBulb, Outlet, DimmingLight]] = {}
# Key format: "{serial_number}.{output_number:02X}"
# Example: "0020044991.00"
# Usage: on_datapoint_received() uses this to update specific accessory states

# Registry 2: Lookup by (module_type_code, link_number) (NEW - for event-driven refresh)
module_registry: Dict[tuple[int, int], List[Union[LightBulb, Outlet, DimmingLight]]] = {}
# Key format: (module_type_code, link_number)
# Example: (7, 2) → [LightBulb("0020044991.00"), LightBulb("0020044991.01"), ...]
# Usage: handle_module_state_changed() uses this for O(1) lookup by module
# Note: One module can have multiple accessories (different output_numbers)
```

**Both registries are populated during `add_room()` / `build_bridge()`:**
```python
# Existing code
self.accessory_registry[accessory.identifier] = accessory

# NEW code to add
module_key = (accessory.module.module_type_code, accessory.module.link_number)
if module_key not in self.module_registry:
    self.module_registry[module_key] = []
self.module_registry[module_key].append(accessory)
```

#### Advantages
- Centralized event handling in HAP service
- Dual-key registry enables O(1) lookup by both `serial_number.output` and `(module_type_code, link_number)`
- HAP service coordinates state refresh for all affected accessories
- Clean separation: HAP service orchestrates, cache service handles invalidation

#### Implementation Flow

1. **Event Reception**: `EventTelegramReceivedEvent` dispatched with telegram payload `E12L01I83MAK`
2. **Parse Event**: Extract `module_type_code=12`, `link_number=01`, `input_number=03`
3. **Dispatch Event**: Dispatch `ModuleStateChangedEvent` with parsed event telegram data
4. **HAP Service Handling**: `HomekitHapService.handle_module_state_changed()` receives event
5. **Accessory Lookup**: O(1) lookup via `module_registry.get((event.module_type_code, event.link_number), [])`
6. **Cache Refresh Request**: For each matching accessory, dispatch `ReadDatapointEvent` with `refresh_cache=True`
7. **Cache Invalidation**: Cache service sees `refresh_cache=True`, invalidates entry, forwards to protocol
8. **State Update**: Fresh state received from protocol, cache updated, accessory state updated via `on_datapoint_received()`

#### New Event: ModuleStateChangedEvent

```python
class ModuleStateChangedEvent(BaseEvent):
    """Event dispatched when a module's state changes (from event telegram)"""

    module_type_code: int = Field(description="Module type code from event telegram")
    link_number: int = Field(description="Link number from event telegram")
    input_number: int = Field(description="Input number that triggered the event")
    event_type: str = Field(description="Event type (M=press, B=release)")
```

#### Updated ReadDatapointEvent

```python
class ReadDatapointEvent(DatapointEvent):
    refresh_cache: bool = Field(
        default=False,
        description="If True, force cache invalidation and fresh protocol query"
    )
```

#### Code Example: HomeKitService

```python
def dispatch_event_telegram_received_event(self, event: TelegramReceivedEvent) -> None:
    """Parse and dispatch event telegram as ModuleStateChangedEvent"""
    self.logger.debug("Event telegram received, parsing...")
    event_telegram = self.telegram_service.parse_event_telegram(event.frame)

    self.logger.debug(
        f"Parsed event: module_type={event_telegram.module_type}, "
        f"link={event_telegram.link_number}, input={event_telegram.input_number}"
    )

    # Dispatch to accessories
    self.event_bus.dispatch(
        ModuleStateChangedEvent(
            module_type_code=event_telegram.module_type,
            link_number=event_telegram.link_number,
            input_number=event_telegram.input_number,
            event_type=event_telegram.event_type.value if event_telegram.event_type else "M"
        )
    )
```

#### Code Example: HomekitHapService

```python
class HomekitHapService:
    def __init__(self, homekit_config, module_service, event_bus):
        self.event_bus = event_bus
        self.accessory_registry: Dict[str, Union[LightBulb, Outlet, DimmingLight]] = {}
        self.module_registry: Dict[tuple[int, int], List[Union[LightBulb, Outlet, DimmingLight]]] = {}

        # Subscribe to module state changes
        self.event_bus.on(ModuleStateChangedEvent, self.handle_module_state_changed)

    def handle_module_state_changed(self, event: ModuleStateChangedEvent) -> None:
        """Handle module state change by refreshing affected accessories"""
        self.logger.debug(
            f"Module state changed: module_type={event.module_type_code}, "
            f"link={event.link_number}, input={event.input_number}"
        )

        # O(1) lookup using module_registry
        module_key = (event.module_type_code, event.link_number)
        affected_accessories = self.module_registry.get(module_key, [])

        if not affected_accessories:
            self.logger.debug(
                f"No accessories found for module_type={event.module_type_code}, "
                f"link={event.link_number}"
            )
            return

        # Request cache refresh for each affected accessory
        for accessory in affected_accessories:
            self.logger.info(
                f"Requesting cache refresh for accessory: {accessory.identifier}"
            )

            # Request OUTPUT_STATE refresh
            self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=accessory.module.serial_number,
                    datapoint_type=DataPointType.OUTPUT_STATE,
                    refresh_cache=True
                )
            )

            # If dimming light, also refresh LIGHT_LEVEL
            if isinstance(accessory, DimmingLight):
                self.event_bus.dispatch(
                    ReadDatapointEvent(
                        serial_number=accessory.module.serial_number,
                        datapoint_type=DataPointType.LIGHT_LEVEL,
                        refresh_cache=True
                    )
                )
```

#### Code Example: HomeKitCacheService

```python
def handle_read_datapoint_event(self, event: ReadDatapointEvent) -> None:
    """Handle ReadDatapointEvent by checking cache or refresh flag"""

    # Check if cache refresh requested
    if event.refresh_cache:
        self.logger.info(
            f"Cache refresh requested: serial={event.serial_number}, "
            f"type={event.datapoint_type}"
        )
        # Invalidate cache entry
        cache_key = self._get_cache_key(event.serial_number, event.datapoint_type)
        if cache_key in self.cache:
            del self.cache[cache_key]
            self.logger.debug(f"Invalidated cache entry: {cache_key}")

        # Force protocol query
        self.event_bus.dispatch(
            ReadDatapointFromProtocolEvent(
                serial_number=event.serial_number,
                datapoint_type=event.datapoint_type,
            )
        )
        return

    # Normal cache lookup flow
    cached_event = self._get_cached_event(event.serial_number, event.datapoint_type)
    if cached_event:
        self.event_bus.dispatch(cached_event)
    else:
        self.event_bus.dispatch(
            ReadDatapointFromProtocolEvent(
                serial_number=event.serial_number,
                datapoint_type=event.datapoint_type,
            )
        )
```

## Implementation Plan

**Files to Modify:**

1. **`src/xp/models/protocol/conbus_protocol.py`**
   - Add `ModuleStateChangedEvent` class
   - Add `refresh_cache: bool` field to `ReadDatapointEvent` (default: False)

2. **`src/xp/services/homekit/homekit_service.py`**
   - Modify `dispatch_event_telegram_received_event()` to parse event telegram
   - Dispatch `ModuleStateChangedEvent` with parsed event data

3. **`src/xp/services/homekit/homekit_hap_service.py`**
   - Add `module_registry: Dict[tuple[int, int], List[...]]` instance variable
   - Modify `add_room()` to populate both `accessory_registry` and `module_registry`
   - Add handler for `ModuleStateChangedEvent`
   - Implement `handle_module_state_changed()` to:
     - Lookup `module_registry.get((module_type_code, link_number), [])`
     - For each matching accessory, dispatch `ReadDatapointEvent(refresh_cache=True)`
     - Handle DimmingLight accessories (also refresh LIGHT_LEVEL)

4. **`src/xp/services/homekit/homekit_cache_service.py`**
   - Modify `handle_read_datapoint_event()` to check `refresh_cache` flag
   - Implement cache invalidation when `refresh_cache=True`

5. **`tests/unit/test_services/test_homekit_cache_service.py`**
   - Test `ReadDatapointEvent` with `refresh_cache=True` invalidates cache
   - Test `ReadDatapointEvent` with `refresh_cache=False` uses cache
   - Test cache invalidation only affects specified entry

6. **`tests/unit/test_services/test_homekit_hap_service.py`**
   - Test `ModuleStateChangedEvent` triggers refresh for matching accessories
   - Test `ModuleStateChangedEvent` ignored when no accessories match
   - Test multiple accessories on same module all get refreshed
   - Test DimmingLight accessories get both OUTPUT_STATE and LIGHT_LEVEL refreshed

### Dependencies

**Required Services:**
- `TelegramService` (for parsing event telegrams in HomeKitService)

**New Events:**
- `ModuleStateChangedEvent` (to be created)

**Modified Events:**
- `ReadDatapointEvent` (add `refresh_cache` field)

**Existing Events:**
- `EventTelegramReceivedEvent` (already dispatched in `homekit_service.py:156`)

### Event Flow Diagram

```
[Physical Button Press]
         ↓
[XP Module generates Event: E12L01I83MAK]
         ↓
[TelegramProtocol receives via TCP]
         ↓
[TelegramReceivedEvent dispatched]
         ↓
[HomeKitService.handle_telegram_received()]
         ↓
[Parse event telegram → extract module_type_code=12, link_number=01]
         ↓
[Dispatch ModuleStateChangedEvent] ← NEW
         ↓
[HomekitHapService.handle_module_state_changed()] ← NEW
         ↓
[O(1) lookup: module_registry.get((12, 01))]
         ↓
[Found matching LightBulb(s) for module_type_code=12, link=01]
         ↓
[For each matching accessory:]
         ↓
[Dispatch ReadDatapointEvent(refresh_cache=True)] ← NEW FLAG
         ↓
[HomeKitCacheService sees refresh_cache=True] ← MODIFIED
         ↓
[Invalidate cache entry for (serial_number, OUTPUT_STATE)]
         ↓
[Dispatch ReadDatapointFromProtocolEvent]
         ↓
[Fresh protocol query → OutputStateReceivedEvent]
         ↓
[Cache updated with fresh state]
         ↓
[HomekitHapService.on_datapoint_received() updates accessory.is_on]
         ↓
[HomeKit UI shows updated state]
```

## Testing Requirements

### Unit Tests

1. **ModuleStateChangedEvent Dispatching**
   - Test `dispatch_event_telegram_received_event()` parses event telegram correctly
   - Test `ModuleStateChangedEvent` dispatched with correct `module_type_code`, `link_number`, `input_number`
   - Test both button press (M) and release (B) events

2. **HAP Service Event Handling**
   - Test `HomekitHapService.handle_module_state_changed()` uses module_registry for lookup
   - Test matching accessories found via `module_registry.get((module_type_code, link_number))`
   - Test `ReadDatapointEvent(refresh_cache=True)` dispatched for matching LightBulb
   - Test `ReadDatapointEvent(refresh_cache=True)` dispatched for matching Outlet
   - Test DimmingLight gets both OUTPUT_STATE and LIGHT_LEVEL refresh requests
   - Test no refresh request when no accessories match (empty list returned)

3. **Cache Refresh Flag**
   - Given: Cache contains `(serial_number, OUTPUT_STATE)` entry
   - When: `ReadDatapointEvent(refresh_cache=True)` received
   - Then: Cache entry removed and `ReadDatapointFromProtocolEvent` dispatched

4. **Cache Normal Operation**
   - Given: Cache contains `(serial_number, OUTPUT_STATE)` entry
   - When: `ReadDatapointEvent(refresh_cache=False)` received
   - Then: Cached event returned, no protocol query

5. **Cache Entry Isolation**
   - Given: Cache contains entries for multiple serial numbers and datapoint types
   - When: `ReadDatapointEvent(refresh_cache=True)` for specific entry
   - Then: Only that specific entry is removed, others remain

### Integration Tests

1. **End-to-End Event-Driven Cache Refresh**
   - Setup: Populate cache with module state (OUTPUT_STATE = OFF)
   - Action: Dispatch `EventTelegramReceivedEvent` for button press on module
   - Verify: `ModuleStateChangedEvent` dispatched
   - Verify: HAP service finds matching accessory in registry
   - Verify: `ReadDatapointEvent(refresh_cache=True)` dispatched
   - Verify: Cache invalidated
   - Verify: Protocol query triggered
   - Verify: Fresh state received and cached
   - Verify: `on_datapoint_received()` updates accessory state

2. **Multi-Accessory Scenario**
   - Setup: Multiple accessories (LightBulb, Outlet) for different modules in registry
   - Action: `ModuleStateChangedEvent` for module A
   - Verify: Only accessories for module A get refresh requests
   - Verify: Accessories for other modules are not affected

## Configuration Changes

No changes required to configuration file formats. Accessories already have access to `ConsonModuleConfig` which contains `module_type_code` and `link_number`.

## References

- **Event Telegram Model**: `src/xp/models/telegram/event_telegram.py`
- **Telegram Protocol**: `src/xp/services/protocol/telegram_protocol.py:78` (Event telegram example)
- **HomeKit Service**: `src/xp/services/homekit/homekit_service.py:155-157` (Event forwarding)
- **HAP Service**: `src/xp/services/homekit/homekit_hap_service.py` (Accessory registry and state updates)
- **Cache Service**: `src/xp/services/homekit/homekit_cache_service.py`
- **Conson Config**: `src/xp/models/homekit/homekit_conson_config.py`
- **Existing Cache Spec**: `doc/Feat-Bubus-Caching.md`
- **Protocol Events**: `src/xp/models/protocol/conbus_protocol.py:155-158`

## Success Criteria

- ✅ Event telegrams are parsed and dispatched as `ModuleStateChangedEvent`
- ✅ `HomekitHapService` subscribes to `ModuleStateChangedEvent`
- ✅ HAP service uses `module_registry` for O(1) lookup by `(module_type_code, link_number)`
- ✅ Dual-key registries (`accessory_registry` and `module_registry`) maintained during build
- ✅ HAP service dispatches `ReadDatapointEvent(refresh_cache=True)` for each match
- ✅ DimmingLight accessories get both OUTPUT_STATE and LIGHT_LEVEL refresh
- ✅ Cache service invalidates entry when `refresh_cache=True` flag is set
- ✅ Fresh protocol query triggered after cache invalidation
- ✅ `on_datapoint_received()` updates accessory state with fresh data
- ✅ Non-matching accessories not affected (no unnecessary queries)
- ✅ Unit test coverage ≥ 90% for new code
- ✅ Integration tests verify end-to-end event-driven cache refresh
- ✅ No performance degradation (cache operations remain efficient)
