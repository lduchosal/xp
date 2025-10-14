# Feature: Bus Debounce and Query Deduplication

## Problem Statement

When a physical button press triggers an Event Telegram, multiple identical query telegrams are sent on the Conbus protocol. This happens because:

1. A single module (e.g., `module_type_code=12, link_number=01`) may control multiple HomeKit accessories
2. Each accessory triggers its own `ReadDatapointEvent(refresh_cache=True)`
3. Each event flows through the cache service independently
4. Each results in a separate `ReadDatapointFromProtocolEvent`
5. Each triggers `telegram_protocol.sendFrame()` with the **same telegram**

### Example Scenario

**Configuration:**
```yaml
# Module 012345678901 has 4 outputs configured as separate accessories
- name: "Living Room Light 1"
  serial_number: "012345678901"
  output_number: 0

- name: "Living Room Light 2"
  serial_number: "012345678901"
  output_number: 1

- name: "Living Room Light 3"
  serial_number: "012345678901"
  output_number: 2

- name: "Living Room Light 4"
  serial_number: "012345678901"
  output_number: 3
```

**Event Flow:**
```
[Physical Button Press on Module]
         ↓
[Event Telegram: E12L01I83MAK]
         ↓
[ModuleStateChangedEvent(module_type=12, link=01)]
         ↓
[HomekitHapService.handle_module_state_changed()]
         ↓
[O(1) lookup finds 4 matching accessories]
         ↓
[For accessory 1: ReadDatapointEvent(serial="012345678901", type=OUTPUT_STATE, refresh=True)]
[For accessory 2: ReadDatapointEvent(serial="012345678901", type=OUTPUT_STATE, refresh=True)]
[For accessory 3: ReadDatapointEvent(serial="012345678901", type=OUTPUT_STATE, refresh=True)]
[For accessory 4: ReadDatapointEvent(serial="012345678901", type=OUTPUT_STATE, refresh=True)]
         ↓
[Cache service invalidates and forwards each event]
         ↓
[4× ReadDatapointFromProtocolEvent with identical parameters]
         ↓
[4× telegram_protocol.sendFrame(b"S012345678901F02D12")] ← DUPLICATE!
```

**Result:** The same telegram `S012345678901F02D12` is sent **4 times** unnecessarily.

### Impact

- **Protocol Overhead**: Wastes bus bandwidth with redundant queries
- **Module Load**: Target module processes the same request multiple times
- **Latency**: Delays other legitimate requests waiting in queue
- **Resource Usage**: Unnecessary CPU and network I/O

## Proposed Solution: Request Deduplication with Debounce Window

Implement a **telegram request queue** with deduplication logic that:

1. **Batches requests** within a configurable debounce window (e.g., 50ms)
2. **Deduplicates identical telegrams** before sending to protocol
3. **Broadcasts responses** to all waiting listeners
4. **Maintains request order** for different telegrams

### Architecture

```
[Multiple ReadDatapointFromProtocolEvent]
         ↓
[TelegramDebounceService]
    ├─ Request Queue (with dedup key)
    ├─ Debounce Timer (50ms window)
    └─ Pending Response Registry
         ↓
[Batch Processing]
    ├─ Deduplicate by (serial_number, system_function, datapoint_type)
    ├─ Send unique telegrams only
    └─ Map responses back to all original requesters
         ↓
[telegram_protocol.sendFrame()] ← ONCE per unique telegram
         ↓
[TelegramReceivedEvent with response]
         ↓
[Broadcast to all waiting events] ← Multiple OutputStateReceivedEvent
```

### Key Components

#### 1. TelegramDebounceService

New service that sits between `HomeKitConbusService` and `TelegramProtocol`:

```python
class TelegramDebounceService:
    """
    Debounces and deduplicates outgoing telegram requests.

    Collects requests in a short time window (default 50ms) and only
    sends unique telegrams to the protocol layer.
    """

    def __init__(
        self,
        event_bus: EventBus,
        telegram_protocol: TelegramProtocol,
        debounce_ms: int = 50
    ):
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol
        self.debounce_ms = debounce_ms

        # Queue of pending requests
        self.request_queue: Dict[str, List[ReadDatapointFromProtocolEvent]] = {}
        self.timer_handle: Optional[asyncio.TimerHandle] = None

        # Subscribe to protocol events
        self.event_bus.on(
            ReadDatapointFromProtocolEvent,
            self.handle_read_datapoint_request
        )

    def handle_read_datapoint_request(
        self,
        event: ReadDatapointFromProtocolEvent
    ) -> None:
        """Queue request and start/reset debounce timer"""

        # Create dedup key
        dedup_key = self._create_dedup_key(event)

        # Add to queue
        if dedup_key not in self.request_queue:
            self.request_queue[dedup_key] = []
        self.request_queue[dedup_key].append(event)

        self.logger.debug(
            f"Queued request: {dedup_key} "
            f"(queue size: {len(self.request_queue[dedup_key])})"
        )

        # Reset debounce timer
        if self.timer_handle:
            self.timer_handle.cancel()

        self.timer_handle = asyncio.get_event_loop().call_later(
            self.debounce_ms / 1000.0,
            lambda: asyncio.create_task(self._process_queue())
        )

    def _create_dedup_key(
        self,
        event: ReadDatapointFromProtocolEvent
    ) -> str:
        """Create unique key for deduplication"""
        return f"{event.serial_number}:{event.datapoint_type.value}"

    async def _process_queue(self) -> None:
        """Process all queued requests, send unique telegrams"""

        if not self.request_queue:
            return

        self.logger.info(
            f"Processing request queue: {len(self.request_queue)} unique telegrams, "
            f"{sum(len(events) for events in self.request_queue.values())} total requests"
        )

        # Process each unique telegram
        for dedup_key, events in self.request_queue.items():
            self.logger.debug(
                f"Sending telegram for {dedup_key} "
                f"(consolidating {len(events)} duplicate requests)"
            )

            # Send telegram only ONCE
            event = events[0]  # All events in list are identical
            system_function = SystemFunction.READ_DATAPOINT.value
            datapoint_value = event.datapoint_type.value
            telegram = f"S{event.serial_number}F{system_function}D{datapoint_value}"
            self.telegram_protocol.sendFrame(telegram.encode())

            # Note: Response will be handled by existing flow
            # TelegramReceivedEvent → HomeKitService → OutputStateReceivedEvent
            # All waiting accessories will receive the same cached response

        # Clear queue
        self.request_queue.clear()
        self.timer_handle = None
```

#### 2. Modified Event Flow

```
[ReadDatapointFromProtocolEvent] ← Multiple events from cache service
         ↓
[TelegramDebounceService.handle_read_datapoint_request()]
    ├─ Queue request with dedup_key = "012345678901:12" (OUTPUT_STATE)
    ├─ Start/reset 50ms timer
    └─ Wait for more requests
         ↓
[50ms debounce window expires]
         ↓
[TelegramDebounceService._process_queue()]
    ├─ Found 4 requests with same dedup_key
    ├─ Send telegram ONCE: S012345678901F02D12
    └─ Clear queue
         ↓
[telegram_protocol.sendFrame()] ← ONCE!
         ↓
[TelegramReceivedEvent: R012345678901F02D12xxx]
         ↓
[HomeKitService dispatches OutputStateReceivedEvent]
         ↓
[Cache service caches response]
         ↓
[All 4 accessories read from cache] ← Already populated!
```

## Implementation Plan

### Phase 1: Core Debounce Service

1. **Create `TelegramDebounceService`**
   - File: `src/xp/services/protocol/telegram_debounce_service.py`
   - Implement request queuing with dedup key
   - Implement debounce timer (default 50ms)
   - Subscribe to `ReadDatapointFromProtocolEvent`

2. **Modify `HomeKitConbusService`**
   - Remove direct `ReadDatapointFromProtocolEvent` handler
   - Let `TelegramDebounceService` handle it instead
   - Keep other event handlers (SendActionEvent, SendWriteConfigEvent)

3. **Update Dependency Injection**
   - Register `TelegramDebounceService` in container
   - Ensure it's initialized before `HomeKitConbusService`

### Phase 2: Configuration

4. **Add Debounce Configuration**
   ```yaml
   # config.yaml
   protocol:
     debounce_ms: 50  # Debounce window in milliseconds
     enable_deduplication: true  # Feature flag
   ```

5. **Make Service Optional**
   - If `enable_deduplication: false`, bypass debounce service
   - Useful for debugging/testing

### Phase 3: Testing

6. **Unit Tests**
   ```python
   def test_debounce_deduplicates_identical_requests():
       """Test that multiple identical requests result in single telegram"""

   def test_debounce_preserves_different_requests():
       """Test that different telegrams are all sent"""

   def test_debounce_window_timing():
       """Test that requests within window are batched"""

   def test_debounce_broadcasts_responses():
       """Test that all requesters receive the response"""
   ```

7. **Integration Tests**
   ```python
   def test_multiple_accessories_single_telegram():
       """Test 4 accessories on same module send 1 telegram"""

   def test_mixed_datapoint_types_preserved():
       """Test OUTPUT_STATE and LIGHT_LEVEL are not deduplicated"""
   ```

### Phase 4: Observability

8. **Add Metrics**
   - `telegrams_queued`: Total requests queued
   - `telegrams_sent`: Unique telegrams sent
   - `telegrams_deduped`: Requests deduplicated
   - `debounce_batches`: Number of batch processing cycles

9. **Add Logging**
   ```python
   self.logger.info(
       f"Debounce batch processed: "
       f"{telegrams_sent} sent, "
       f"{telegrams_deduped} deduplicated "
       f"(saved {(telegrams_deduped/telegrams_queued)*100:.1f}%)"
   )
   ```

## Design Considerations

### Deduplication Key

The dedup key must uniquely identify equivalent telegrams:

```python
dedup_key = f"{serial_number}:{datapoint_type.value}"
```

**Examples:**
- `"012345678901:12"` → OUTPUT_STATE for module 012345678901
- `"012345678901:15"` → LIGHT_LEVEL for module 012345678901
- `"987654321098:12"` → OUTPUT_STATE for different module

This ensures:
- ✅ Multiple OUTPUT_STATE requests for same module → deduplicated
- ✅ OUTPUT_STATE + LIGHT_LEVEL for same module → NOT deduplicated (different datapoints)
- ✅ Same datapoint for different modules → NOT deduplicated

### Debounce Window Tuning

**Trade-offs:**

| Window | Pros | Cons |
|--------|------|------|
| 10ms | Lower latency | Less batching, fewer dedup opportunities |
| 50ms | Good balance | Acceptable latency for most use cases |
| 100ms | Maximum dedup | Noticeable UI lag |

**Recommendation:** Start with **50ms**, make configurable.

### Ordering Guarantees

**Within same dedup key:**
- Only the first request is sent (all are identical)
- Order doesn't matter (same telegram, same response)

**Across different dedup keys:**
- Preserve insertion order
- Process in FIFO order within each batch

### Event Telegram Handling

**Question:** Should we also debounce ACTION telegrams (SendActionEvent)?

**Answer:** **NO** - Action telegrams should be sent immediately:
- User-initiated actions (button press in HomeKit app)
- Low frequency (human interaction speed)
- Latency-sensitive (user expects immediate feedback)

Only debounce **query telegrams** (ReadDatapointFromProtocolEvent).

### Response Broadcasting

**Current Flow:**
```
[Telegram sent]
  ↓
[Response received: R012345678901F02D12x0x1x1x0]
  ↓
[OutputStateReceivedEvent dispatched]
  ↓
[Cache service caches response]
  ↓
[All accessories read from cache] ← Works with existing architecture!
```

**No changes needed** - The existing cache service already handles broadcasting:
1. First query updates cache
2. Subsequent queries hit cache immediately
3. All accessories eventually get the same data

## Success Metrics

### Before Implementation

```
Event Telegram Received: E12L01I83MAK
├─ 4 accessories found for module (12, 01)
├─ 4× ReadDatapointEvent dispatched
├─ 4× ReadDatapointFromProtocolEvent dispatched
└─ 4× sendFrame("S012345678901F02D12") ← WASTEFUL
```

**Telegrams sent:** 4
**Unique telegrams:** 1
**Waste:** 75%

### After Implementation

```
Event Telegram Received: E12L01I83MAK
├─ 4 accessories found for module (12, 01)
├─ 4× ReadDatapointEvent dispatched
├─ 4× ReadDatapointFromProtocolEvent queued
├─ Debounce window (50ms)
└─ 1× sendFrame("S012345678901F02D12") ← EFFICIENT!
```

**Telegrams sent:** 1
**Unique telegrams:** 1
**Waste:** 0%
**Improvement:** 75% reduction in bus traffic

## Alternative Approaches Considered

### Alternative 1: Deduplicate at Cache Service

**Approach:** Let cache service detect duplicate refresh requests.

**Pros:**
- Simpler, fewer moving parts
- No new service required

**Cons:**
- Cache service becomes protocol-aware (violates separation of concerns)
- Harder to tune debounce window
- Less reusable for other event types

**Verdict:** ❌ Not recommended

### Alternative 2: Deduplicate at HomekitHapService

**Approach:** Only dispatch one ReadDatapointEvent per unique (serial, datapoint) tuple.

**Pros:**
- Prevents duplicate events at source
- No protocol-layer changes

**Cons:**
- Requires tracking which accessories need updates
- Complex bookkeeping
- Misses deduplication opportunities from other sources

**Verdict:** ❌ Not recommended

### Alternative 3: Debounce Service (Proposed)

**Approach:** Dedicated service at protocol boundary for request deduplication.

**Pros:**
- Clean separation of concerns
- Reusable for any telegram type
- Easy to configure/disable
- Protocol-aware layer (appropriate location)

**Cons:**
- New service to maintain
- Adds latency (acceptable with small window)

**Verdict:** ✅ **Recommended**

## Future Enhancements

### Request Coalescing Across Datapoint Types

Currently, OUTPUT_STATE and LIGHT_LEVEL are separate telegrams. Could we combine them?

**Example:**
```python
# Instead of:
S012345678901F02D12  # OUTPUT_STATE
S012345678901F02D15  # LIGHT_LEVEL

# Send:
S012345678901F02D12,D15  # Combined query (if protocol supports)
```

**Blocker:** Requires protocol support for multi-datapoint queries.

### Adaptive Debounce Window

Adjust debounce window based on traffic patterns:
- Low traffic → shorter window (lower latency)
- High traffic → longer window (more batching)

### Priority Queuing

Some telegrams may be more urgent:
- User-initiated actions: High priority, no debounce
- Auto-refresh queries: Low priority, debounce aggressively

## References

- Event Flow Diagram: `doc/architecture/Feat-Cache-Management.md`
- Cache Service: `src/xp/services/homekit/homekit_cache_service.py`
- Protocol Service: `src/xp/services/homekit/homekit_conbus_service.py`
- Telegram Protocol: `src/xp/services/protocol/telegram_protocol.py`

## Open Questions

1. **Should debounce be applied to all ReadDatapoint requests, or only those with `refresh_cache=True`?**
   - Recommendation: All requests (normal cache misses can also be deduplicated)

2. **What happens if protocol response is lost/timeout during debounce?**
   - Current behavior: Timeout handled by protocol layer
   - No change needed: All waiting requests will fail together

3. **Should we expose debounce metrics via API/CLI?**
   - Recommendation: Yes, add to `xp conbus stats` command

## Status

- ✅ Problem identified and documented
- ✅ Solution designed
- ⏳ Implementation pending
- ⏳ Testing pending
- ⏳ Deployment pending
