# Feature: Persistent HomeKit Cache

## Overview

Add disk persistence to `HomeKitCacheService` to prevent cache rebuilding on restart, reducing protocol query load during initialization.

## Problem Statement

Current `HomeKitCacheService` stores cache in memory only:
- Service restart → cache lost
- HomeKit queries → protocol overload during cache rebuild
- Slow initialization with many accessories

**Impact**: Every restart triggers full cache rebuild via protocol queries.

## Proposed Solution

Persist cache to disk in `.cache/homekit_cache.json`:
- Load cache on service initialization
- Save cache on every update
- Use JSON serialization for Pydantic compatibility
- Atomic writes to prevent corruption

## Implementation

### File Location

```
.cache/
└── homekit_cache.json
```

**Format**:
```json
{
  "0020044991.OUTPUT_STATE": {
    "event": {
      "serial_number": "0020044991",
      "datapoint_type": "OUTPUT_STATE",
      "data_value": 1
    },
    "timestamp": "2025-10-12T10:30:00.123456"
  }
}
```

### Code Changes

**File**: `src/xp/services/homekit/homekit_cache_service.py`

**Add imports**:
```python
import json
from pathlib import Path
from typing import Any
```

**Add constants**:
```python
CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "homekit_cache.json"
```

**Modify `__init__`**:
```python
def __init__(self, event_bus: EventBus, enable_persistence: bool = True):
    self.logger = logging.getLogger(__name__)
    self.event_bus = event_bus
    self.cache: dict[tuple[str, DataPointType], CacheEntry] = {}
    self.enable_persistence = enable_persistence

    # Load cache from disk
    if self.enable_persistence:
        self._load_cache()

    # Register event handlers
    self.event_bus.on(ReadDatapointEvent, self.handle_read_datapoint_event)
    self.event_bus.on(OutputStateReceivedEvent, self.handle_output_state_received_event)
    self.event_bus.on(LightLevelReceivedEvent, self.handle_light_level_received_event)

    self.logger.info(f"HomeKitCacheService initialized with {len(self.cache)} cached entries")
```

**Note**: `enable_persistence=False` can be used in tests to disable disk I/O.

**Add persistence methods**:
```python
def _serialize_cache_key(self, key: tuple[str, DataPointType]) -> str:
    """Serialize cache key to JSON-compatible string."""
    serial_number, datapoint_type = key
    return f"{serial_number}.{datapoint_type.value}"

def _deserialize_cache_key(self, key_str: str) -> tuple[str, DataPointType]:
    """Deserialize cache key from JSON string."""
    serial_number, datapoint_type_str = key_str.rsplit(".", 1)
    return (serial_number, DataPointType(datapoint_type_str))

def _serialize_cache(self) -> dict[str, Any]:
    """Serialize cache to JSON-compatible dict."""
    serialized = {}
    for key, entry in self.cache.items():
        key_str = self._serialize_cache_key(key)
        serialized[key_str] = {
            "event": entry["event"].model_dump(mode="json"),
            "timestamp": entry["timestamp"].isoformat(),
        }
    return serialized

def _deserialize_cache(self, data: dict[str, Any]) -> dict[tuple[str, DataPointType], CacheEntry]:
    """Deserialize cache from JSON dict."""
    cache: dict[tuple[str, DataPointType], CacheEntry] = {}
    for key_str, entry_data in data.items():
        try:
            key = self._deserialize_cache_key(key_str)
            event_data = entry_data["event"]

            # Reconstruct event based on datapoint_type
            if key[1] == DataPointType.OUTPUT_STATE:
                event = OutputStateReceivedEvent(**event_data)
            elif key[1] == DataPointType.LIGHT_LEVEL:
                event = LightLevelReceivedEvent(**event_data)
            else:
                self.logger.warning(f"Unknown datapoint type in cache: {key[1]}")
                continue

            cache[key] = {
                "event": event,
                "timestamp": datetime.fromisoformat(entry_data["timestamp"]),
            }
        except Exception as e:
            self.logger.warning(f"Failed to deserialize cache entry {key_str}: {e}")
            continue

    return cache

def _load_cache(self) -> None:
    """Load cache from disk."""
    if not CACHE_FILE.exists():
        self.logger.debug("No cache file found, starting with empty cache")
        return

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)

        self.cache = self._deserialize_cache(data)
        self.logger.info(f"Loaded {len(self.cache)} entries from cache file")
    except Exception as e:
        self.logger.error(f"Failed to load cache from disk: {e}")
        self.cache = {}

def _save_cache(self) -> None:
    """Save cache to disk atomically."""
    if not self.enable_persistence:
        return

    try:
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_file = CACHE_FILE.with_suffix(".tmp")
        with temp_file.open("w") as f:
            json.dump(self._serialize_cache(), f, indent=2)

        # Atomic rename
        temp_file.replace(CACHE_FILE)

        self.logger.debug(f"Saved {len(self.cache)} entries to cache file")
    except Exception as e:
        self.logger.error(f"Failed to save cache to disk: {e}")
```

**Modify `_cache_event`** (add save call):
```python
def _cache_event(
    self, event: Union[OutputStateReceivedEvent, LightLevelReceivedEvent]
) -> None:
    """Store an event in the cache."""
    cache_key = self._get_cache_key(event.serial_number, event.datapoint_type)
    cache_entry: CacheEntry = {
        "event": event,
        "timestamp": datetime.now(),
    }
    self.cache[cache_key] = cache_entry
    self.logger.debug(
        f"Cached event: serial={event.serial_number}, "
        f"type={event.datapoint_type}, value={event.data_value}"
    )

    # Persist to disk
    self._save_cache()
```

**Modify `clear_cache`** (add save call):
```python
def clear_cache(self) -> None:
    """Clear all cached entries."""
    self.logger.info("Clearing cache")
    self.cache.clear()
    self._save_cache()
```

**Modify cache invalidation in `handle_read_datapoint_event`** (add save call):
```python
if event.refresh_cache:
    self.logger.info(...)
    cache_key = self._get_cache_key(event.serial_number, event.datapoint_type)
    if cache_key in self.cache:
        del self.cache[cache_key]
        self.logger.debug(f"Invalidated cache entry: {cache_key}")
        self._save_cache()  # Persist invalidation
```

### .gitignore Update

Add to `.gitignore`:
```
# Cache directory
/.cache/
```

## Dependencies

**Standard Library**:
- `json` - JSON serialization (already used in project)
- `pathlib.Path` - File path handling (already used in project)

**No new external dependencies required.**

## Testing

### Unit Tests

**File**: `tests/unit/test_services/test_homekit_cache_service.py`

Add tests:
- ✅ Test cache persistence: cache saved after event
- ✅ Test cache loading: service loads existing cache on init
- ✅ Test cache invalidation: invalidated entries removed from disk
- ✅ Test corrupt cache handling: graceful degradation on JSON errors
- ✅ Test missing cache file: service starts with empty cache
- ✅ Test atomic writes: verify `.tmp` file usage

### Integration Tests

**File**: `tests/integration/test_cache_persistence_integration.py`

Add tests:
- ✅ End-to-end: cache persists across service restarts
- ✅ Multi-entry: verify all entries persist correctly
- ✅ Concurrent writes: verify atomic writes prevent corruption

## Quality Checklist

### Coding Standards (see `doc/Coding.md`)
- ✅ Type hints: All methods fully typed
- ✅ Error handling: Graceful degradation on file I/O errors
- ✅ Logging: DEBUG for I/O, INFO for cache stats
- ✅ No sensitive data: Serial numbers only (not credentials)

### Architecture Compliance (see `doc/Architecture.md`)
- ✅ Service pattern: Persistence logic encapsulated in service
- ✅ Dependency injection: No new dependencies required
- ✅ Event-driven: Cache updates triggered by events (existing)
- ✅ Layer separation: File I/O isolated in service methods

### Quality Requirements (see `doc/Quality.md`)
- ✅ Test coverage: ≥75% for new code
- ✅ Type safety: Strict mypy compliance
- ✅ Line length: 88 characters (Black)
- ✅ Must pass: `pdm check`

### Dependency Management
- ✅ No circular dependencies
- ✅ Only standard library additions (`json`, `pathlib`)
- ✅ No external package dependencies
- ✅ Backward compatible: service works without cache file

## Performance Considerations

- **Load time**: O(n) where n = cache entries (~10-100ms for 100 entries)
- **Save time**: O(n) write + atomic rename (~20-50ms)
- **Disk usage**: ~500 bytes per entry (JSON overhead)
- **Optimization**: Save throttling could be added if needed (not in MVP)

## Success Criteria

- ✅ Cache persists across service restarts
- ✅ No protocol overload on restart (cache hit rate >90%)
- ✅ Graceful handling of missing/corrupt cache files
- ✅ Atomic writes prevent corruption
- ✅ Unit test coverage ≥90% for new code
- ✅ Integration tests verify end-to-end persistence
- ✅ No performance degradation (<100ms overhead)
- ✅ Must pass `pdm check` (lint, format, typecheck, test)

## References

- **Cache Service**: `src/xp/services/homekit/homekit_cache_service.py`
- **Event Models**: `src/xp/models/protocol/conbus_protocol.py`
- **DataPoint Types**: `src/xp/models/telegram/datapoint_type.py`
- **Related Spec**: `doc/architecture/Feat-Cache-Management.md` (event-driven cache)
