# HomeKit Cache Service

Improve performance for frequently accessed Conson module data by implementing intelligent caching

## Cli usage

Commands:
```
xp cache get <key> <tags>
xp cache set <key> <tags> <data>
xp cache clear [key|tags]
xp cache items
```

Output:
```
Cached items :
- key : data
- key : data
- key : data
- key : data
```

**CLI checklist:**
- [ ] Add `cache` command group to main CLI
- [ ] Add `get`, `set`, `clear`, `items` subcommands
- [ ] Use HomeKitCacheService for all cache operations
- [ ] Add CLI command in `src/xp/cli/commands/cache_commands.py`
- [ ] Register command in `src/xp/cli/main.py`
- [ ] As few as possible logic in cli, prefer logic in service

## Service

`HomeKitCacheService` to handle intelligent caching of expensive Conson module queries:

- Cache frequently accessed output states from `ConbusOutputService.get_output_state`
- Implement event-based invalidation
- Persist cache data for faster startup times
- Provide cache statistics and management

Key methods:
- `get(key: str, tag: str) -> CacheResponse`
- `set(tag: str, tag: str, data: str) -> None`
- `clear(tag: str) -> None`
- `clear(key: str = None) -> None`

**Implementation checklist:**
- [ ] Create `HomeKitCacheService` class in `src/xp/services/homekit_cache_service.py`
- [ ] Define `CacheResponse` models in `src/xp/models/cache.py`
- [ ] Implement simple TTL expiration
- [ ] Implement file-based persistence for cache data
- [ ] Add event-based cache invalidation when device states change
- [ ] Integrate with existing `ConbusOutputService` for cache misses
- [ ] Add cache key generation based on `key` and `tags`
- [ ] Implement tag-based cache expiration

## Cache Strategy

```python

class CacheEntry:
    data: str
    timestamp: datetime
    tags: List[str]
    ttl: int

def get(self, key: str, tag: str) -> CacheResponse:
    cache_key = f"{key}"

    if cache_key in cache and not expired:
        return CacheResponse(data=cached_data, hit=True)

    # Cache miss - query device
    data = ConbusOutputService.get_output_state(key)
    cache[cache_key] = CacheEntry(data=data, tags=[tag], ttl=300)

    return CacheResponse(data=data, hit=False)
```

## Expiration Strategy

```python
def received_event(self, event: str) -> None:
    # Invalidate all cache entries tagged with this event
    for key, entry in cache.items():
        if event in entry.tags:
            cache.pop(key)

def received_update(self, serial_number: str, event: str, data: str) -> None:
    # Update cache with fresh data while preserving tags
    cache_key = f"{serial_number}:{event}"
    if cache_key in cache:
        cache[cache_key].data = data
        cache[cache_key].timestamp = datetime.now()

    if not cache_key in cache:
        cache[cache_key] = CacheEntry(data=data, tags=[event], ttl=300)

```

## Persistence

- Cache data persisted to `~/.homekit_cache.json`
- Automatic save on cache updates
- Load cache on service startup
- Configurable cache directory and TTL settings

## Tests

CLI integration tests in `tests/integration/test_cache_integration.py`:

- `test_cache_get_hit()` - Test cache hit scenario
- `test_cache_get_miss()` - Test cache miss and device query
- `test_cache_set()` - Test manual cache entry creation
- `test_cache_received_event()` - Test event-based invalidation
- `test_cache_clear()` - Test cache clearing functionality
- `test_cache_persistence()` - Test file-based persistence

**Test checklist:**
- [ ] Test CLI command parsing and execution
- [ ] Test service caching functionality with TTL
- [ ] Test event-based cache invalidation
- [ ] Test file persistence and recovery
- [ ] Test error handling scenarios and device failures


