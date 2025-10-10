# Conbus Request Performance Optimization

## Problem Analysis

The HomeKit integration makes multiple synchronous TCP requests to Conbus modules for each accessory interaction:

1. **Synchronous blocking calls**: Every HomeKit get/set operation blocks until TCP response
2. **No caching**: Each status check (`get_on()`) triggers fresh TCP request to module
3. **Connection overhead**: New TCP socket per request in `ConbusService:79-119`
4. **Network latency**: 2-second receive timeout on every request (`ConbusService:178`)
5. **Sequential processing**: Multiple accessories = multiple sequential TCP calls

### Code Impact Points
- `homekit_module_service.py:102` - `get_output_state()` for every `get_on()`
- `homekit_lightbulb.py:58` - Direct dispatcher call triggers TCP request
- `conbus_service.py:208-279` - TCP socket creation/teardown per request

## Solution Architecture

### 1. **Request Caching Layer**
```
Cache TTL: 500ms for status, 100ms for actions
- Cache `get_output_state()` responses by serial_number
- Invalidate cache on `send_action()` for same module
- Background refresh for frequently accessed modules
```

### 2. **Async Request Batching**
```
Batch multiple status requests into single TCP call
- Aggregate requests over 50ms window
- Single response telegram with multiple module states
- Reduce network round-trips significantly
```

### 3. **Background State Sync**
```
Proactive status polling for active accessories
- 2-second interval for recently used accessories
- Listen to EventTelegram broadcasts from modules
- Reduces reactive request latency to near-zero
```

## Implementation Priority

1. **Immediate (Week 1)**: Add response caching to `ConbusOutputService`
2. **Medium-term (Month 1)**: Request batching for bulk operations
3. **Long-term (Month 2)**: Background state synchronization

## Expected Impact

- **Response time**: 2000ms → 50ms for cached requests
- **Connection overhead**: 90% reduction in TCP handshakes
- **Network traffic**: 60% reduction through batching
- **UI responsiveness**: Near-instant status updates