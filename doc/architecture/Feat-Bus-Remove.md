# Feature Specification: Remove bubus Dependency

## Status: COMPLETED

**Completed:** 2026-01-03

## Overview

This document provides a comprehensive overview of all code that still uses the `bubus` event bus library. The goal is to migrate away from this dependency to an alternative solution.

**Key insight:** The entire `xp.services.homekit` folder (14 files) has been replaced by `xp.services.term.homekit_service.py` which uses `psygnal.Signal` instead of `bubus.EventBus`. Removing this folder eliminates most bubus usage.

## Summary of Changes

### Files Deleted (21 total)
- 14 source files in `src/xp/services/homekit/`
- 5 test files for old homekit services
- 1 script (`scripts/twistedbus.py`)
- 2 protocol files (`telegram_protocol.py`, `protocol_factory.py`)

### Files Updated (5 total)
- `src/xp/utils/dependencies.py` - Removed old registrations
- `src/xp/cli/commands/homekit/homekit_start_commands.py` - Uses new HomekitService
- `src/xp/cli/commands/homekit/homekit.py` - Removed validator commands
- `src/xp/models/protocol/conbus_protocol.py` - Changed BaseEvent to BaseModel
- `src/xp/services/protocol/__init__.py` - Removed TelegramProtocol reference
- `pyproject.toml` - Removed bubus dependency

### Results
- All 1333 tests pass
- Typecheck passes (295 source files)
- bubus completely removed from codebase

---

## Phase 0: Remove xp.services.homekit (Quick Win)

The old HomeKit implementation uses bubus and can be completely removed since `xp.services.term` provides a replacement using psygnal.

### Comparison: Old vs New HomeKit

| Aspect | Old (`xp.services.homekit`) | New (`xp.services.term`) |
|--------|----------------------------|--------------------------|
| Class | `HomeKitService` (capital K) | `HomekitService` (lowercase k) |
| Event system | `bubus.EventBus` | `psygnal.Signal` |
| Protocol | `TelegramProtocol` + bubus | `ConbusEventProtocol` |
| Sub-services | 8+ separate services | Single service + driver |
| Files | 14 files | 2 files |

### Files to DELETE

#### Source Files (14 files)
- [ ] `src/xp/services/homekit/__init__.py`
- [ ] `src/xp/services/homekit/homekit_cache_service.py`
- [ ] `src/xp/services/homekit/homekit_conbus_service.py`
- [ ] `src/xp/services/homekit/homekit_conson_validator.py`
- [ ] `src/xp/services/homekit/homekit_config_validator.py`
- [ ] `src/xp/services/homekit/homekit_dimminglight.py`
- [ ] `src/xp/services/homekit/homekit_dimminglight_service.py`
- [ ] `src/xp/services/homekit/homekit_hap_service.py`
- [ ] `src/xp/services/homekit/homekit_lightbulb.py`
- [ ] `src/xp/services/homekit/homekit_lightbulb_service.py`
- [ ] `src/xp/services/homekit/homekit_module_service.py`
- [ ] `src/xp/services/homekit/homekit_outlet.py`
- [ ] `src/xp/services/homekit/homekit_outlet_service.py`
- [ ] `src/xp/services/homekit/homekit_service.py`

#### Test Files (5 files)
- [ ] `tests/unit/test_services/test_homekit_services.py`
- [ ] `tests/unit/test_services/test_homekit_cache_service.py`
- [ ] `tests/unit/test_services/test_homekit_config_validator.py`
- [ ] `tests/unit/test_services/test_homekit_conson_service.py`
- [ ] `tests/integration/test_homekit_config_integration.py`

#### Scripts (1 file)
- [ ] `scripts/twistedbus.py` - Uses old HomeKitService

### Files to UPDATE

#### dependencies.py - Remove old homekit registrations
```
Lines to remove:
- Line 58-65: Old homekit imports
- Lines 467-475: HomekitHapService registration
- Lines 571-593: HomeKitLightbulbService, HomeKitOutletService, HomeKitDimmingLightService
- Lines 597-612: HomeKitCacheService, HomeKitConbusService
- Lines 620-636: HomeKitService registration
- Lines 453-458: EventBus registration (after TelegramProtocol update)
- Lines 540-563: TelegramProtocol and TelegramFactory (use ConbusEventProtocol instead)
```

#### CLI Commands
- [ ] `src/xp/cli/commands/homekit/homekit_start_commands.py`
  - Update to use `xp.services.term.homekit_service.HomekitService`
- [ ] `src/xp/cli/commands/homekit/homekit.py`
  - Remove ConfigValidationService import (lines 45, 109)

### Cascade Effect: Protocol Layer Cleanup

After removing `xp.services.homekit`, the following become unused:

#### TelegramProtocol (can be removed/simplified)
Only used by:
1. ~~HomeKitConbusService~~ (deleted)
2. TelegramFactory (only used by old HomeKitService)

**Action:** Remove `TelegramProtocol` and `TelegramFactory` entirely since `ConbusEventProtocol` is the replacement.

#### Files to DELETE (Protocol layer)
- [ ] `src/xp/services/protocol/telegram_protocol.py` - Replace with ConbusEventProtocol
- [ ] `src/xp/services/protocol/protocol_factory.py` - No longer needed

#### conbus_protocol.py Events (still needed)
The event classes in `conbus_protocol.py` are still used by `ConbusEventProtocol` and other services. However, they can be migrated from `bubus.BaseEvent` to `pydantic.BaseModel` since the new protocol doesn't use bubus event dispatching.

---

## Current Usage Summary

- **Total files using bubus:** 25 files
- **Source files:** 14 files
- **Test files:** 5 files
- **Documentation files:** 3 files
- **Configuration files:** 2 files

## Bubus Imports Analysis

Two main imports from bubus:
1. `from bubus import EventBus` - Event bus instance for pub/sub messaging
2. `from bubus import BaseEvent` - Base class for event definitions

---

## Migration Checklist

### Source Files

#### Core Infrastructure

- [ ] **`src/xp/utils/dependencies.py`**
  - Line 4: `from bubus import EventBus`
  - Lines 454-458: EventBus singleton registration
  - Lines 472, 543, 558, 574, 582, 590, 600, 608, 624: EventBus injection into services
  - **Impact:** Central DI container - all EventBus instances originate here

- [ ] **`src/xp/models/protocol/conbus_protocol.py`**
  - Line 7: `from bubus import BaseEvent`
  - All event classes inherit from `BaseEvent`:
    - `ConnectionMadeEvent` (line 19)
    - `ConnectionFailedEvent` (line 32)
    - `SendWriteConfigEvent` (line 43)
    - `SendActionEvent` (line 60)
    - `DatapointEvent` (line 79)
    - `ModuleEvent` (line 134)
    - `LightBulbGetOnEvent` (line 166)
    - `OutletSetInUseEvent` (line 195)
    - `ConnectionLostEvent` (line 242)
    - `TelegramEvent` (line 253)
    - `ModuleStateChangedEvent` (line 282)
    - `InvalidTelegramReceivedEvent` (line 317)
  - **Impact:** All protocol events depend on BaseEvent

#### Protocol Services

- [ ] **`src/xp/services/protocol/telegram_protocol.py`**
  - Line 12: `from bubus import EventBus`
  - Line 40: `event_bus: EventBus` class attribute
  - Line 42: `def __init__(self, event_bus: EventBus, ...)`
  - **Usage:** Publishes telegram events via event_bus

- [ ] **`src/xp/services/protocol/protocol_factory.py`**
  - Line 9: `from bubus import EventBus`
  - Line 34: `event_bus: EventBus` in constructor
  - **Usage:** Factory creates protocols with event_bus reference

#### HomeKit Services

- [ ] **`src/xp/services/homekit/homekit_service.py`**
  - Line 13: `from bubus import EventBus`
  - Line 60: `event_bus: EventBus` in constructor
  - **Usage:** Main HomeKit service orchestration

- [ ] **`src/xp/services/homekit/homekit_hap_service.py`**
  - Line 13: `from bubus import EventBus`
  - Line 56: `event_bus: EventBus` class attribute
  - Line 62: `event_bus: EventBus` in constructor
  - **Usage:** HAP bridge service with event bus

- [ ] **`src/xp/services/homekit/homekit_cache_service.py`**
  - Line 9: `from bubus import EventBus`
  - Line 47: `event_bus: EventBus` in constructor
  - **Usage:** Caches datapoint events, intercepts read events

- [ ] **`src/xp/services/homekit/homekit_conbus_service.py`**
  - Line 9: `from bubus import EventBus`
  - Line 31: `event_bus: EventBus` class attribute
  - Line 33: `event_bus: EventBus` in constructor
  - **Usage:** Handles conbus protocol events

- [ ] **`src/xp/services/homekit/homekit_lightbulb_service.py`**
  - Line 9: `from bubus import EventBus`
  - Line 29: `event_bus: EventBus` class attribute
  - Line 31: `def __init__(self, event_bus: EventBus)`
  - **Usage:** Handles lightbulb on/off events

- [ ] **`src/xp/services/homekit/homekit_outlet_service.py`**
  - Line 9: `from bubus import EventBus`
  - Line 30: `event_bus: EventBus` class attribute
  - Line 32: `def __init__(self, event_bus: EventBus)`
  - **Usage:** Handles outlet on/off events

- [ ] **`src/xp/services/homekit/homekit_dimminglight_service.py`**
  - Line 9: `from bubus import EventBus`
  - Line 31: `event_bus: EventBus` class attribute
  - Line 33: `def __init__(self, event_bus: EventBus)`
  - **Usage:** Handles dimming light brightness events

#### HomeKit Accessories

- [ ] **`src/xp/services/homekit/homekit_lightbulb.py`**
  - Line 9: `from bubus import EventBus`
  - Line 38: `event_bus: EventBus` class attribute
  - Line 45: `event_bus: EventBus` in constructor
  - **Usage:** Lightbulb HAP accessory

- [ ] **`src/xp/services/homekit/homekit_outlet.py`**
  - Line 9: `from bubus import EventBus`
  - Line 42: `event_bus: EventBus` class attribute
  - Line 49: `event_bus: EventBus` in constructor
  - **Usage:** Outlet HAP accessory

- [ ] **`src/xp/services/homekit/homekit_dimminglight.py`**
  - Line 9: `from bubus import EventBus`
  - Line 42: `event_bus: EventBus` class attribute
  - Line 49: `event_bus: EventBus` in constructor
  - **Usage:** Dimming light HAP accessory

---

### Test Files

- [ ] **`tests/unit/test_services/test_homekit_services.py`**
  - Line 6: `from bubus import EventBus`
  - **Usage:** Creates mock EventBus for testing

- [ ] **`tests/unit/test_services/test_telegram_protocol.py`**
  - Line 9: `from bubus import EventBus`
  - **Usage:** Creates mock EventBus for testing

- [ ] **`tests/unit/test_services/test_protocol.py`**
  - Line 7: `from bubus import EventBus`
  - **Usage:** Creates mock EventBus for testing

- [ ] **`tests/unit/test_services/test_homekit_cache_service.py`**
  - Line 5: `from bubus import EventBus`
  - **Usage:** Creates mock EventBus for testing

- [ ] **`tests/unit/test_utils/test_logging.py`**
  - Contains bubus reference (verify context)

- [ ] **`tests/unit/test_models/test_logger_config.py`**
  - Contains bubus reference (verify context)

---

### Documentation Files

- [ ] **`doc/Architecture.md`**
  - Line 57: Reference to `BaseEvent from bubus`
  - **Action:** Update architecture documentation

- [ ] **`doc/conbus/Feat-Bubus-Caching.md`**
  - Multiple references to bubus throughout
  - **Action:** Update or archive documentation

- [ ] **`doc/architecture/Feat-Cache-Management.md`**
  - Contains bubus references
  - **Action:** Update documentation

---

### Configuration Files

- [ ] **`pyproject.toml`**
  - Line 19: `"bubus>=1.5.6"` dependency
  - **Action:** Remove dependency after migration

- [ ] **`config/logger.yml.example`**
  - Contains bubus reference (logger configuration)
  - **Action:** Update logger configuration

---

## Migration Strategy

### Phase 1: Choose Alternative
- [ ] Evaluate alternatives (e.g., `psygnal`, custom implementation, `blinker`)
- [ ] Document chosen approach

### Phase 2: Core Migration
- [ ] Create adapter/compatibility layer
- [ ] Migrate `BaseEvent` usages in `conbus_protocol.py`
- [ ] Migrate `EventBus` in `dependencies.py`

### Phase 3: Service Migration
- [ ] Migrate protocol services (telegram_protocol, protocol_factory)
- [ ] Migrate HomeKit services (6 service files)
- [ ] Migrate HomeKit accessories (3 accessory files)

### Phase 4: Test Updates
- [ ] Update all test files (5 files)
- [ ] Ensure test coverage remains complete

### Phase 5: Cleanup
- [ ] Update documentation (3 files)
- [ ] Remove bubus from `pyproject.toml`
- [ ] Update configuration files

---

## Event Bus Usage Patterns

The codebase uses bubus for:

1. **Event Publishing:** Services publish events (e.g., `event_bus.emit(event)`)
2. **Event Subscription:** Services subscribe to event types (e.g., `event_bus.on(EventType, handler)`)
3. **Event Inheritance:** All events extend `BaseEvent` for type safety

### Key Event Flows

```
TelegramProtocol
    ├── emits: TelegramEvent, ConnectionMadeEvent, ConnectionLostEvent
    └── emits: InvalidTelegramReceivedEvent

HomeKitConbusService
    ├── subscribes: ReadDatapointFromProtocolEvent
    └── emits: OutputStateReceivedEvent, LightLevelReceivedEvent

HomeKitCacheService
    ├── subscribes: ReadDatapointEvent, OutputStateReceivedEvent, LightLevelReceivedEvent
    └── emits: ReadDatapointFromProtocolEvent (cache miss)

HomeKitLightbulbService
    ├── subscribes: LightBulbSetOnEvent, LightBulbGetOnEvent
    └── emits: SendActionEvent, ReadDatapointEvent

HomeKitOutletService
    ├── subscribes: OutletSetOnEvent, OutletGetOnEvent, OutletGetInUseEvent
    └── emits: SendActionEvent, ReadDatapointEvent

HomeKitDimmingLightService
    ├── subscribes: DimmingLightSetOnEvent, DimmingLightSetBrightnessEvent, etc.
    └── emits: SendActionEvent, SendWriteConfigEvent, ReadDatapointEvent
```

---

## Notes

- The `psygnal` library is already a dependency (`psygnal>=0.15.0` in pyproject.toml) and could be considered as an alternative
- Total event classes to migrate: ~20+ event types in `conbus_protocol.py`
- Careful attention needed for event priority/ordering in cache service

---

## Summary: Remaining bubus Usage After Phase 0

After removing `xp.services.homekit` folder, TelegramProtocol, and TelegramFactory:

### Still Using bubus (3 files)

| File | Usage | Action |
|------|-------|--------|
| `src/xp/models/protocol/conbus_protocol.py` | `BaseEvent` inheritance | Migrate to `pydantic.BaseModel` |
| `tests/unit/test_services/test_telegram_protocol.py` | Tests for deleted file | DELETE |
| `tests/unit/test_services/test_protocol.py` | Tests for protocol | UPDATE |

### Final Cleanup

1. **conbus_protocol.py:** Change `from bubus import BaseEvent` to use `pydantic.BaseModel`
   - All 20+ event classes already use Pydantic fields
   - Only change needed: base class inheritance

2. **pyproject.toml:** Remove `"bubus>=1.5.6"` dependency

3. **Documentation:** Update references in:
   - `doc/Architecture.md`
   - `doc/conbus/Feat-Bubus-Caching.md`
   - `doc/architecture/Feat-Cache-Management.md`

### Expected Result

After completing all phases:
- **0 files** importing from bubus
- **bubus** removed from dependencies
- Simpler codebase using only `psygnal` for signals and `pydantic` for models
