# HomeKit Cache Service Background Refresh

Implement background refresh functionality to return stale cache values immediately while updating cache in the background for optimal performance.

## Overview

Enhance the existing HomeKit Cache Service with background refresh capability to provide instant responses while ensuring data freshness. When a cache entry is near expiration (within refresh threshold), return the stale value immediately and trigger a background update.

## Cli usage

Commands (enhanced existing commands):
```
xp cache get <key> <tag> // always background-refresh if needed
xp cache set <key> <tag> <data> // refresh-threshold default existing ttl=300
xp cache items
```

Output:
```
{
  "key": "device123",
  "tag": "output_state",
  "hit": true,
  "data": "ON",
  "stale": true,
  "refresh_triggered": true,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**CLI checklist:**
- [ ] Enhance existing CLI commands in `src/xp/cli/commands/cache_commands.py`
- [ ] Add configuration persistence for background refresh settings

## Service Enhancement

Enhance `HomeKitCacheService` with background refresh capabilities:

- Return stale values immediately when within refresh threshold
- Trigger background device queries for cache updates
- Manage background worker threads for non-blocking updates
- Provide refresh threshold configuration per cache entry
- Track refresh status and statistics

Key methods (enhanced/new):
- `_trigger_background_refresh(key: str, tag: str) -> None`
- `_background_refresh_worker(key: str, tag: str) -> None`

**Implementation checklist:**
- [ ] Add refresh threshold support to `CacheEntry` model
- [ ] Implement background thread pool for refresh operations
- [ ] Add `RefreshStats` model in `src/xp/models/cache.py`
- [ ] Enhance `CacheResponse` with `stale` and `refresh_triggered` fields
- [ ] Implement graceful shutdown of background workers
- [ ] Add thread-safe cache operations with proper locking
- [ ] Track refresh statistics (success/failure rates, timing)

## Background Refresh Strategy

```python
def get(self, key: str, tag: str, background_refresh: bool = True) -> CacheResponse:
    cache_key = key

    if cache_key in cache:
        entry = cache[cache_key]

        # Calculate time until expiration
        time_remaining = entry.ttl - (datetime.now() - entry.timestamp).total_seconds()

        if time_remaining > 0:
            # Cache hit - check if refresh needed
            if background_refresh and time_remaining <= entry.refresh_threshold:
                # Return stale data immediately, trigger background refresh
                self._trigger_background_refresh(key, tag)
                return CacheResponse(
                    data=entry.data,
                    hit=True,
                    stale=True,
                    refresh_triggered=True
                )
            else:
                # Fresh cache hit
                return CacheResponse(data=entry.data, hit=True, stale=False)
        else:
            # Expired - remove and fall through to fresh fetch
            del cache[cache_key]

    # Cache miss or expired - fetch fresh data
    data = ConbusOutputService.get_output_state(key)
    cache[cache_key] = CacheEntry(
        data=data,
        tags=[tag],
        ttl=300,
        refresh_threshold=60  # Refresh in background when 60s remaining
    )

    return CacheResponse(data=data, hit=False, stale=False)
```

## Background Worker Management

```python
class BackgroundRefreshManager:
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_refreshes = set()  # Track ongoing refreshes
        self.refresh_stats = RefreshStats()

    def trigger_refresh(self, key: str, tag: str, callback: callable):
        refresh_id = f"{key}:{tag}"

        if refresh_id not in self.active_refreshes:
            self.active_refreshes.add(refresh_id)
            future = self.executor.submit(self._refresh_worker, key, tag, callback)
            future.add_done_callback(lambda f: self.active_refreshes.discard(refresh_id))

    def _refresh_worker(self, key: str, tag: str, callback: callable):
        try:
            # Perform background refresh
            fresh_data = ConbusOutputService.get_output_state(key)
            callback(key, tag, fresh_data, success=True)
            self.refresh_stats.record_success()
        except Exception as e:
            callback(key, tag, None, success=False, error=str(e))
            self.refresh_stats.record_failure()
```

## Configuration Management

```python
class CacheConfig:
    def __init__(self):
        self.background_refresh_enabled = True
        self.default_refresh_threshold = 60  # seconds
        self.max_background_workers = 3
        self.refresh_timeout = 10  # seconds

    def load_from_file(self, config_file: str):
        # Load configuration from JSON/YAML file
        pass

    def save_to_file(self, config_file: str):
        # Save configuration to persistent storage
        pass
```

## Enhanced Models

```python
class CacheEntry:
    def __init__(self, data: str, tags: List[str], ttl: int = 300, refresh_threshold: int = 60):
        self.data = data
        self.timestamp = datetime.now()
        self.tags = tags
        self.ttl = ttl
        self.refresh_threshold = refresh_threshold  # New field
        self.last_refresh_attempt = None
        self.refresh_in_progress = False

class CacheResponse:
    def __init__(self, data: Any, hit: bool, stale: bool = False,
                 refresh_triggered: bool = False, error: Optional[str] = None):
        self.data = data
        self.hit = hit
        self.stale = stale  # New field
        self.refresh_triggered = refresh_triggered  # New field
        self.error = error
        self.timestamp = datetime.now()

class RefreshStats:
    def __init__(self):
        self.total_refreshes = 0
        self.successful_refreshes = 0
        self.failed_refreshes = 0
        self.average_refresh_time = 0.0
        self.last_refresh_time = None
```

## Configuration Persistence

- Background refresh settings persisted to `~/.homekit_cache_config.json`
- Automatic configuration loading on service startup
- Runtime configuration updates via CLI commands
- Per-entry refresh threshold overrides

## Performance Considerations

- **Thread Safety**: Use proper locking for cache operations during background updates
- **Resource Management**: Limit concurrent background refresh operations
- **Error Handling**: Graceful fallback when background refresh fails
- **Memory Usage**: Monitor and limit background worker memory consumption
- **Startup Time**: Fast service initialization without blocking on background threads

## Tests

CLI integration tests in `tests/integration/test_cache_background_refresh_integration.py`:

- `test_background_refresh_stale_return()` - Test immediate stale value return
- `test_background_refresh_cache_update()` - Test background cache update
- `test_background_refresh_disabled()` - Test with background refresh disabled
- `test_refresh_threshold_configuration()` - Test refresh threshold settings
- `test_concurrent_background_refreshes()` - Test multiple concurrent refreshes
- `test_background_refresh_error_handling()` - Test error scenarios
- `test_cache_config_persistence()` - Test configuration save/load

Unit tests in `tests/unit/test_services/test_background_refresh_manager.py`:

- `test_refresh_worker_success()` - Test successful background refresh
- `test_refresh_worker_failure()` - Test background refresh failure handling
- `test_concurrent_refresh_prevention()` - Test duplicate refresh prevention
- `test_worker_thread_cleanup()` - Test proper thread cleanup
- `test_refresh_statistics_tracking()` - Test refresh stats collection

**Test checklist:**
- [ ] Test background refresh trigger conditions
- [ ] Test stale value return with refresh triggered
- [ ] Test background worker thread management
- [ ] Test configuration persistence and loading
- [ ] Test error handling in background operations
- [ ] Test performance under concurrent refresh scenarios
- [ ] Test graceful service shutdown with active background workers
- [ ] Test refresh statistics accuracy and reporting

## Migration Strategy

1. **Backward Compatibility**: Existing cache functionality remains unchanged by default
2. **Gradual Rollout**: Background refresh can be enabled per cache entry or globally
3. **Configuration Migration**: Automatic creation of default configuration on first use
4. **Performance Monitoring**: Add metrics to track background refresh effectiveness

## Security Considerations

- **Resource Limits**: Prevent excessive background worker creation
- **Error Logging**: Avoid logging sensitive data in background refresh errors
- **Thread Isolation**: Ensure background operations don't affect main cache operations
- **Timeout Management**: Prevent hanging background operations