# Feature Specification: Bubus Message Caching

## Overview

Implement a caching mechanism for bubus protocol messages to reduce redundant protocol queries and improve response time for frequently accessed datapoints.

## Problem Statement

Currently, every `ReadDatapointEvent` triggers a protocol query via telegram frame transmission. This results in:
- Network overhead for repeated queries of the same datapoint
- Increased response latency
- Unnecessary protocol traffic

## Current Flow

1. `ReadDatapointEvent` is dispatched with `serial_number` and `datapoint_type`
2. `HomeKitConbusService.handle_read_datapoint_event()` converts it to a telegram frame
3. Telegram frame is sent via `telegram_protocol.sendFrame()`
4. Protocol responds with `OutputStateReceivedEvent` or `LightLevelReceivedEvent`
5. Event is dispatched to listeners

**Reference:**
- Event models: `src/xp/models/protocol/conbus_protocol.py:43-57`
- Handler: `src/xp/services/homekit/homekit_conbus_service.py:31-37`

## Proposed Solution

Implement a cache service that intercepts bubus events and stores recent datapoint responses.

### Cache Structure

Cache entries are keyed by `(serial_number, datapoint_type)` tuple and store:

```python
{
    "event": OutputStateReceivedEvent | LightLevelReceivedEvent,
    "timestamp": datetime,  # for future TTL support
}
```

### Event Interception Flow

#### 1. Cache Write Operations

**Intercept and cache:**
- `OutputStateReceivedEvent` (has: `serial_number`, `datapoint_type`, `data_value`)
- `LightLevelReceivedEvent` (has: `serial_number`, `datapoint_type`, `data_value`)

Both events extend `DatapointEvent` which provides `serial_number` and `datapoint_type` fields.

**On interception:**
1. Extract cache key: `(event.serial_number, event.datapoint_type)`
2. Store event object in cache with current timestamp
3. Allow event to continue propagating (non-blocking)

#### 2. Cache Read Operations

**Intercept queries:**
- `ReadDatapointEvent` (has: `serial_number`, `datapoint_type`)

**On interception:**
1. Extract cache key: `(event.serial_number, event.datapoint_type)`
2. Check if key exists in cache
3. **If match found:**
   - Return cached `OutputStateReceivedEvent` or `LightLevelReceivedEvent`
   - Do NOT forward to protocol handler
   - Dispatch cached event to original requester
4. **If no match:**
   - Forward `ReadDatapointEvent` to protocol handler as normal
   - Response will be cached when received

### Matching Logic

```
Cache Key = (serial_number, datapoint_type)

Match occurs when:
  ReadDatapointEvent.serial_number == CachedEvent.serial_number
  AND
  ReadDatapointEvent.datapoint_type == CachedEvent.datapoint_type
```

## Implementation Considerations

### Service Architecture

Create `BubusCacheService` that:
1. Subscribes to events with higher priority than `HomeKitConbusService`
2. Maintains in-memory cache dictionary
3. Decides whether to forward or respond from cache

### Event Priority

- `BubusCacheService` must register with **higher priority** than `HomeKitConbusService`
- This ensures cache check happens before protocol query

### Cache Invalidation Strategy

**Phase 1 (Initial):**
- Cache entries never expire (infinite TTL)
- Cache grows unbounded

**Future Enhancement:**
- Add TTL configuration (e.g., 30 seconds)
- Clear stale entries on timer
- Add manual cache invalidation API

### Cache Bypass

Consider adding a flag to `ReadDatapointEvent` for force refresh:
```python
class ReadDatapointEvent(DatapointEvent):
    bypass_cache: bool = False  # Future enhancement
```

## Benefits

1. **Reduced Protocol Traffic:** Eliminate duplicate queries for same datapoint
2. **Improved Response Time:** Return cached values immediately without network roundtrip
3. **Lower Network Load:** Fewer telegram frames transmitted
4. **Better Scalability:** System can handle higher query rates

## Testing Requirements

1. **Unit Tests:**
   - Cache stores events correctly
   - Cache key generation matches correctly
   - Cache hit returns stored event
   - Cache miss forwards to protocol

2. **Integration Tests:**
   - Cached events prevent protocol calls
   - Fresh queries reach protocol when cache empty
   - Multiple cached datapoints coexist correctly

3. **Test Scenarios:**
   - Query datapoint → cache miss → store response → query again → cache hit
   - Different serial numbers don't collide
   - Different datapoint types don't collide

## Implementation Steps

1. ✅ Create `HomeKitCacheService` class
2. ✅ Implement cache storage (dict with tuple keys)
3. ✅ Create `ReadDatapointFromProtocolEvent` for internal protocol forwarding
4. ✅ Modify `HomeKitConbusService` to listen to `ReadDatapointFromProtocolEvent`
5. ✅ Register event handlers in cache service
6. ✅ Implement cache write logic for received events
7. ✅ Implement cache read/forward logic for query events
8. ✅ Add logging for cache hits/misses
9. ✅ Write unit tests (12 test cases)
10. ✅ Update service initialization in dependency injection container
11. ✅ Update existing tests for modified services

## Implementation Summary

**Status:** ✅ Complete

The caching mechanism has been successfully implemented with the following components:

1. **New Event:** `ReadDatapointFromProtocolEvent` (conbus_protocol.py:60-63)
   - Internal event for cache misses to forward to protocol

2. **Cache Service:** `HomeKitCacheService` (homekit_cache_service.py)
   - Maintains in-memory cache with (serial_number, datapoint_type) keys
   - Intercepts `ReadDatapointEvent` and checks cache
   - Caches `OutputStateReceivedEvent` and `LightLevelReceivedEvent`
   - Includes cache management methods (clear_cache, get_cache_stats)

3. **Modified Service:** `HomeKitConbusService` (homekit_conbus_service.py:27-28)
   - Now listens to `ReadDatapointFromProtocolEvent` instead of `ReadDatapointEvent`
   - Protocol queries only happen on cache misses

4. **Dependency Injection:** Updated in dependencies.py:395-403
   - Cache service registered before conbus service for proper initialization order
   - Integrated into HomeKitService constructor

5. **Tests:** 12 unit tests in test_homekit_cache_service.py
   - All tests passing ✅
   - Coverage: cache hit/miss, key uniqueness, cache operations

## Future Enhancements

- TTL-based cache expiration
- Cache statistics (hit rate, miss rate tracking)
- Cache size limits (LRU eviction)
- Cache bypass flag in ReadDatapointEvent
- Cache warming on startup
- Persistent cache across restarts
