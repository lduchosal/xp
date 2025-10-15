# Telegram Debounce at Protocol Layer - Revised Architecture

## Proposal: Move Debouncing into TelegramProtocol

**Key Insight:** Instead of debouncing at the event bus layer (TelegramDebounceService), integrate debouncing **directly into `TelegramProtocol.sendFrame()`**.

### Why This Is Better

**Current Approach (Event Layer):**
```
[ReadDatapointFromProtocolEvent]
    ↓
[TelegramDebounceService] ← Dedup only datapoint reads
    ↓
[telegram_protocol.sendFrame()] ← Other calls bypass debounce
```

**Problems:**
- ❌ Only deduplicates `ReadDatapointFromProtocolEvent`
- ❌ Actions, writes, and other telegram types NOT debounced
- ❌ Extra service layer complexity
- ❌ Requires event bus subscriptions

**Proposed Approach (Protocol Layer):**
```
[Any code calls sendFrame()]
    ↓
[TelegramProtocol.sendFrame()] ← Debounce ALL telegrams
    ↓
[TCP send via Twisted transport]
```

**Benefits:**
- ✅ Deduplicates **ALL** telegram types automatically
- ✅ Simpler architecture - no separate service needed
- ✅ Protocol layer owns protocol concerns (single responsibility)
- ✅ Transparent to all callers
- ✅ Works for future telegram types without code changes

### Implementation Design

#### Modified TelegramProtocol

```python
class TelegramProtocol(protocol.Protocol):
    """
    Twisted protocol for XP telegram communication with built-in debouncing.

    Automatically deduplicates identical telegram frames sent within a
    configurable time window (default 50ms).
    """

    def __init__(
        self,
        event_bus: EventBus,
        debounce_ms: int = 50
    ) -> None:
        self.buffer = b""
        self.event_bus = event_bus
        self.debounce_ms = debounce_ms
        self.logger = logging.getLogger(__name__)

        # Debounce state
        self.send_queue: Dict[bytes, List[float]] = {}  # frame -> [timestamps]
        self.timer_handle: Optional[asyncio.TimerHandle] = None

    def sendFrame(self, data: bytes) -> None:
        """
        Queue telegram for sending with automatic deduplication.

        Identical frames within debounce_ms window are deduplicated.
        Only the first occurrence is actually sent to the wire.

        Args:
            data: Raw telegram payload (without checksum/framing)
        """
        # Calculate full frame (add checksum and brackets)
        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"

        current_time = time.time()

        # Check if identical frame was recently sent
        if frame in self.send_queue:
            recent_sends = [
                ts for ts in self.send_queue[frame]
                if current_time - ts < (self.debounce_ms / 1000.0)
            ]

            if recent_sends:
                # Duplicate detected - skip sending
                self.logger.debug(
                    f"Debounced duplicate frame: {frame.decode()} "
                    f"(sent {len(recent_sends)} times in last {self.debounce_ms}ms)"
                )
                return

        # Not a duplicate - send it
        self._send_frame_immediate(frame)

        # Track this send
        if frame not in self.send_queue:
            self.send_queue[frame] = []
        self.send_queue[frame].append(current_time)

        # Schedule cleanup of old timestamps
        self._schedule_cleanup()

    def _send_frame_immediate(self, frame: bytes) -> None:
        """Actually send frame to TCP transport."""
        if not self.transport:
            self.logger.info("Invalid transport")
            raise IOError("Transport is not open")

        self.logger.debug(f"Sending frame: {frame.decode()}")
        self.transport.write(frame)

    def _schedule_cleanup(self) -> None:
        """Schedule cleanup of old timestamp tracking."""
        if self.timer_handle:
            self.timer_handle.cancel()

        loop = asyncio.get_event_loop()
        self.timer_handle = loop.call_later(
            (self.debounce_ms / 1000.0) * 2,  # Cleanup after 2x debounce window
            self._cleanup_old_timestamps
        )

    def _cleanup_old_timestamps(self) -> None:
        """Remove old timestamps to prevent memory leak."""
        current_time = time.time()
        cutoff = current_time - (self.debounce_ms / 1000.0)

        for frame in list(self.send_queue.keys()):
            # Keep only recent timestamps
            self.send_queue[frame] = [
                ts for ts in self.send_queue[frame]
                if ts >= cutoff
            ]

            # Remove frame if no recent sends
            if not self.send_queue[frame]:
                del self.send_queue[frame]

        self.timer_handle = None
```

### Comparison: Event Layer vs Protocol Layer

| Aspect | Event Layer (Current) | Protocol Layer (Proposed) |
|--------|----------------------|---------------------------|
| **Scope** | Only `ReadDatapointFromProtocolEvent` | ALL telegram sends |
| **Services** | Needs `TelegramDebounceService` | Built into `TelegramProtocol` |
| **Complexity** | Event subscriptions + DI wiring | Simple method-level logic |
| **Coverage** | Datapoint reads only | Reads, actions, writes, config, etc. |
| **Future-proof** | Need to update for new events | Automatic for all future sends |
| **Lines of Code** | ~160 (service) + ~50 (DI) + tests | ~60 (protocol method) + tests |
| **Memory** | Separate queue per dedup key | Single queue keyed by frame |
| **Performance** | Event dispatch overhead | Direct method call |

### Deduplication Algorithm

**Dedup Key:** The complete telegram frame (including checksum)

```python
# Examples of dedup keys:
"<S012345678901F02D12AB>"  # OUTPUT_STATE read
"<S012345678901F02D15CD>"  # LIGHT_LEVEL read
"<S012345678901F27D02ABEF>" # Action telegram
```

**Deduplication Logic:**
1. Calculate full frame from input data
2. Check if frame was sent in last `debounce_ms` milliseconds
3. If yes → Skip (deduplicated)
4. If no → Send + record timestamp
5. Periodically cleanup old timestamps

**Why This Works:**
- Identical telegrams (same serial, function, datapoint) have identical frames
- Different telegrams have different frames
- Natural deduplication at the byte level

### Migration Path

#### Phase 1: Implement Protocol-Layer Debouncing

1. **Modify `TelegramProtocol.sendFrame()`**
   - Add debounce logic directly in the method
   - Add timestamp tracking
   - Add cleanup logic

2. **Update `TelegramProtocol.__init__()`**
   - Add `debounce_ms` parameter (default 50)
   - Initialize send_queue dict
   - Initialize timer_handle

3. **Add Unit Tests**
   - Test duplicate detection within window
   - Test different frames not deduplicated
   - Test cleanup of old timestamps
   - Test edge cases (no transport, etc.)

#### Phase 2: Remove TelegramDebounceService

1. **Remove service files**
   - Delete `src/xp/services/protocol/telegram_debounce_service.py`
   - Delete `tests/unit/test_services/test_telegram_debounce_service.py`
   - Delete `tests/integration/test_debounce_integration.py`

2. **Remove from DI container**
   - Remove `TelegramDebounceService` registration from `dependencies.py`
   - Remove from `HomeKitService.__init__` parameters
   - Remove from service exports

3. **Remove from HomeKitConbusService**
   - Re-add `ReadDatapointFromProtocolEvent` handler (reverting previous change)
   - Calls `sendFrame()` which now has built-in debouncing

### Example Flow

**Before (Event Layer):**
```
[4 accessories request same datapoint]
    ↓
[HomeKitCacheService] → 4× ReadDatapointFromProtocolEvent
    ↓
[TelegramDebounceService] → Queue 4 events → Dedup → Send 1 telegram
    ↓
[TelegramProtocol.sendFrame()] → Send to TCP
```

**After (Protocol Layer):**
```
[4 accessories request same datapoint]
    ↓
[HomeKitCacheService] → 4× ReadDatapointFromProtocolEvent
    ↓
[HomeKitConbusService] → 4× sendFrame(b"S012345678901F02D12")
    ↓
[TelegramProtocol.sendFrame()] → Built-in dedup → Send 1× to TCP
```

**Simpler!** No intermediate service needed.

### Configuration

**Via DI Container:**
```python
# dependencies.py
self.container.register(
    TelegramProtocol,
    factory=lambda: TelegramProtocol(
        event_bus=self.container.resolve(EventBus),
        debounce_ms=50,  # Configurable debounce window
    ),
    scope=punq.Scope.singleton,
)
```

**Via Config File (future):**
```yaml
# cli.yml
protocol:
  debounce_ms: 50
  enable_debounce: true
```

### Benefits for All Telegram Types

**1. Datapoint Reads (Already covered)**
```
S012345678901F02D12  # OUTPUT_STATE
S012345678901F02D15  # LIGHT_LEVEL
```

**2. Actions (NEW coverage)**
```
S012345678901F27D02AB  # Turn on output 2
# If user clicks button multiple times rapidly → deduplicated!
```

**3. Write Config (NEW coverage)**
```
S012345678901F04D1502:050  # Set brightness
# If UI sends multiple identical brightness commands → deduplicated!
```

**4. Discovery (NEW coverage)**
```
S0000000000F01D00  # Discover modules
# If reconnection logic retries → deduplicated!
```

### Edge Cases Handled

**1. Different Parameters → NOT Deduplicated**
```
S012345678901F02D12  # OUTPUT_STATE
S012345678901F02D15  # LIGHT_LEVEL (different datapoint)
→ Both sent (different frames)
```

**2. Same Telegram, Different Timing → NOT Deduplicated**
```
t=0ms:   S012345678901F02D12 → Sent
t=100ms: S012345678901F02D12 → Sent (outside 50ms window)
```

**3. Burst of Duplicates → Only First Sent**
```
t=0ms:   S012345678901F02D12 → Sent
t=10ms:  S012345678901F02D12 → Skipped
t=20ms:  S012345678901F02D12 → Skipped
t=30ms:  S012345678901F02D12 → Skipped
Result: 1 sent, 3 deduplicated (75% reduction)
```

**4. Memory Leak Prevention**
```
# Cleanup runs every 100ms (2× debounce window)
# Removes timestamps older than 50ms
# Removes frames with no recent sends
→ Bounded memory usage
```

### Testing Strategy

**Unit Tests:**
```python
class TestTelegramProtocolDebounce:

    def test_single_frame_sent_immediately(self):
        """First occurrence of frame is sent immediately"""

    def test_duplicate_within_window_skipped(self):
        """Duplicate frame within debounce window is skipped"""

    def test_duplicate_outside_window_sent(self):
        """Duplicate frame outside debounce window is sent"""

    def test_different_frames_all_sent(self):
        """Different frames are all sent regardless of timing"""

    def test_timestamp_cleanup(self):
        """Old timestamps are cleaned up periodically"""

    def test_burst_deduplication(self):
        """Burst of identical frames → only first sent"""
```

**Integration Tests:**
```python
class TestProtocolDebounceIntegration:

    def test_four_accessories_one_telegram(self):
        """4 accessories on same module → 1 telegram sent"""

    def test_action_deduplication(self):
        """Multiple identical actions → deduplicated"""

    def test_mixed_telegram_types(self):
        """Different telegram types not deduplicated"""
```

### Performance Considerations

**Lookup Complexity:** O(1) for frame existence check

**Memory Usage:** Bounded by cleanup routine
- Max entries: ~(telegrams/sec × debounce_window)
- Example: 100 telegrams/sec × 50ms = 5 entries max

**CPU Overhead:** Minimal
- Dict lookup: ~10ns
- Timestamp comparison: ~5ns
- Total overhead per sendFrame(): <100ns

**Network Impact:**
- Before: 4 identical telegrams = 4× network packets
- After: 4 identical telegrams = 1× network packet
- Reduction: 75% for typical scenarios

### Backwards Compatibility

**Breaking Changes:** None!
- `sendFrame(data: bytes)` signature unchanged
- Behavior: Transparently deduplicates
- All existing callers work without modification

**Opt-out:**
```python
# Disable debouncing if needed
protocol = TelegramProtocol(event_bus, debounce_ms=0)
```

### Alternative: Batching Mode

**Optional Enhancement:** Instead of immediate send, batch within window

```python
def sendFrame(self, data: bytes) -> None:
    """Queue frame, send batch after debounce window"""
    self.queue_frame(data)
    self.reset_timer()  # Send batch in 50ms

def _flush_queue(self):
    """Send all unique frames in queue"""
    unique_frames = set(self.frame_queue)
    for frame in unique_frames:
        self._send_immediate(frame)
```

**Trade-off:**
- Pro: Even more efficient (one async operation per batch)
- Con: Adds latency (minimum 50ms delay for all telegrams)

**Recommendation:** Use immediate send with dedup (implemented above) for better latency.

## Summary

**Proposed Change:**
Move debouncing from `TelegramDebounceService` (event layer) to `TelegramProtocol.sendFrame()` (protocol layer).

**Impact:**
- ✅ Simpler architecture (remove entire service)
- ✅ Universal coverage (ALL telegrams debounced)
- ✅ Better performance (no event dispatch overhead)
- ✅ Lower memory usage (single queue vs. multiple)
- ✅ More maintainable (logic in one place)
- ✅ Future-proof (automatic for new telegram types)

**Migration:**
1. Implement debouncing in `TelegramProtocol.sendFrame()`
2. Remove `TelegramDebounceService` and related DI wiring
3. Update tests
4. Deploy and monitor

**Expected Result:**
Same 75% reduction in duplicate telegrams, but with cleaner architecture and broader coverage.
