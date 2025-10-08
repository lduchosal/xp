# Chore: Remove Cache Mechanism

This document lists all files and changes required to remove the HomeKitCacheService cache mechanism from the XP project.

## Overview

The cache mechanism was implemented to improve performance for frequently accessed Conson module data. However, it has been decided to remove this functionality and its associated components.

## Files to Remove

### Service Implementation
- **`src/xp/services/homekit/homekit_cache_service.py`**
  - Main service class implementing cache functionality
  - 292 lines of code

### CLI Commands
- **`src/xp/cli/commands/cache_commands.py`**
  - CLI command group for cache operations
  - Commands: get, set, clear, items, stats
  - 214 lines of code

### Models
- **`src/xp/models/cache.py`**
  - Cache data models: `CacheEntry`, `CacheResponse`
  - 103 lines of code

### Tests
- **`tests/unit/test_services/test_homekit_cache_service.py`**
  - Unit tests for HomeKitCacheService

- **`tests/integration/test_cache_integration.py`**
  - Integration tests for cache CLI commands and service

- **`tests/integration/test_homekit_cache_send_action_integration.py`**
  - Integration tests for cache send_action method

- **`tests/unit/test_models/test_cache.py`**
  - Unit tests for cache models (CacheEntry, CacheResponse)

### Documentation
- **`doc/Feat-HomeKit-Cache-Service.md`**
  - Feature documentation for HomeKit Cache Service
  - 127 lines of documentation

- **`doc/Feat-HomeKit-Cache-Service-Background-Refresh.md`**
  - Feature documentation for background refresh functionality

## Files to Modify

### Dependency Injection
- **`src/xp/utils/dependencies.py`**
  - **Line 30**: Remove import `from xp.services.homekit.homekit_cache_service import HomeKitCacheService`
  - **Line 67**: Remove `cache_file` parameter from `__init__` method
  - **Line 78**: Remove `cache_file` parameter documentation
  - **Line 86**: Remove `self._cache_file = cache_file` assignment
  - **Lines 285-296**: Remove HomeKitCacheService registration:
    ```python
    self.container.register(
        HomeKitCacheService,
        factory=lambda: HomeKitCacheService(
            cache_file=self._cache_file,
            conbus_output_service=self.container.resolve(ConbusOutputService),
            conbus_lightlevel_service=self.container.resolve(
                ConbusLightlevelService
            ),
            telegram_service=self.container.resolve(TelegramService),
        ),
        scope=punq.Scope.singleton,
    )
    ```

### CLI Main Entry Point
- **`src/xp/cli/main.py`**
  - **Line 10**: Remove import `from xp.cli.commands.cache_commands import cache`
  - **Line 69**: Remove command registration `cli.add_command(cache)`

### Service Dependencies Graph
- **`doc/Service-Dependencies.dot`**
  - **Line 55**: Remove `HomeKitCacheService;` from HomeKit services cluster
  - **Lines 115-118**: Remove HomeKitCacheService dependency arrows:
    ```
    HomeKitCacheService -> ConbusOutputService;
    HomeKitCacheService -> ConbusLightlevelService;
    HomeKitCacheService -> TelegramService [lhead=cluster_telegram];
    ```

### Git Ignore
- **`.gitignore`**
  - **Line 15**: Remove `.homekit_cache.json` entry

### Test Dependencies
- **`tests/unit/test_utils/test_dependencies.py`**
  - **Line 19**: Remove import `from xp.services.homekit.homekit_cache_service import HomeKitCacheService`
  - **Lines 148-151**: Remove test method `test_resolve_homekit_cache_service()`
  - **Line 206**: Remove `HomeKitCacheService,` from service list validation

## Cache File to Clean Up

- **`.homekit_cache.json`** (if exists in local environments)
  - This is the runtime cache file
  - Already in .gitignore, but may exist on developer machines
  - Should be deleted manually or during deployment

## Impact Analysis

### Dependencies
The cache service has the following dependencies:
- `ConbusOutputService` (used for cache miss fallback)
- `ConbusLightlevelService` (used for brightness operations)
- `TelegramService` (used for event parsing)

No other services depend on `HomeKitCacheService`, so removal is clean.

### CLI Impact
The entire `xp cache` command group will be removed:
- `xp cache get <key> <tag>`
- `xp cache set <key> <tag> <data>`
- `xp cache clear [key_or_tag_or_all]`
- `xp cache items`
- `xp cache stats`

### Service Container Impact
The `ServiceContainer` will no longer:
- Accept `cache_file` parameter
- Register `HomeKitCacheService`
- Create cache file in filesystem

## Migration Notes

- No data migration needed (cache is runtime-only optimization)
- No configuration changes needed in user configs
- Cache file `.homekit_cache.json` can be safely deleted
- All functionality reverts to direct ConBus queries (original behavior)

## Removal Steps

1. Remove all files listed in "Files to Remove" section
2. Update all files listed in "Files to Modify" section
3. Delete any local `.homekit_cache.json` files
4. Run tests to ensure no broken imports or references
5. Update any related documentation that references cache functionality

## Verification Checklist

- [ ] All cache-related files removed
- [ ] All imports of HomeKitCacheService removed
- [ ] CLI cache commands removed from main.py
- [ ] ServiceContainer no longer references cache
- [ ] All cache-related tests removed
- [ ] Service dependency graph updated
- [ ] .gitignore updated
- [ ] No broken imports (run: `python -m pytest tests/`)
- [ ] No references to cache in remaining code (grep for "cache")
- [ ] Documentation updated

## Estimated Effort

- **Files to remove**: 9 files
- **Files to modify**: 4 files
- **Lines of code removed**: ~700+ lines
- **Test coverage impact**: Removal of 3 test files
- **Estimated time**: 1-2 hours

## Alternatives Considered

None - this is a cleanup task to remove unused/unnecessary caching mechanism.