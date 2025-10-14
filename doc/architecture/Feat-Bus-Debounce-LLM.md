# Telegram Debounce Service - Implementation Checklist

**Objective:** Implement request deduplication to prevent sending duplicate telegrams when multiple accessories share the same module.

**Full Specification:** See `doc/architecture/Feat-Bus-Debounce.md`

## Problem Summary

When 4 accessories share module `012345678901`, a single button press sends 4 identical telegrams:
- `S012345678901F02D12` (x4) ❌
- Target: Send once ✅

## Implementation Steps

### Step 1: Create TelegramDebounceService

**File:** `src/xp/services/protocol/telegram_debounce_service.py`

**Requirements:**
```python
class TelegramDebounceService:
    """
    Debounces and deduplicates ReadDatapointFromProtocolEvent requests.
    Batches requests in 50ms window, sends unique telegrams only.
    """

    def __init__(
        self,
        event_bus: EventBus,
        telegram_protocol: TelegramProtocol,
        debounce_ms: int = 50
    )

    def handle_read_datapoint_request(
        self,
        event: ReadDatapointFromProtocolEvent
    ) -> None:
        """Queue request, start/reset debounce timer"""

    def _create_dedup_key(
        self,
        event: ReadDatapointFromProtocolEvent
    ) -> str:
        """Return f"{event.serial_number}:{event.datapoint_type.value}" """

    async def _process_queue(self) -> None:
        """Send unique telegrams, clear queue"""
```

**Key Implementation Details:**
- Use `Dict[str, List[ReadDatapointFromProtocolEvent]]` for request_queue
- Dedup key: `f"{serial_number}:{datapoint_type.value}"`
- Timer: `asyncio.get_event_loop().call_later(debounce_ms/1000.0, callback)`
- Send telegram ONCE per dedup_key using first event in list
- Subscribe to `ReadDatapointFromProtocolEvent` in `__init__`

**Log Messages:**
- DEBUG: "Queued request: {dedup_key} (queue size: {count})"
- INFO: "Processing queue: {unique} unique, {total} total requests"
- DEBUG: "Sending telegram for {dedup_key} (consolidating {count} duplicates)"

### Step 2: Update HomeKitConbusService

**File:** `src/xp/services/homekit/homekit_conbus_service.py`

**Changes:**
- **Remove:** `ReadDatapointFromProtocolEvent` handler registration (line ~27-28)
- **Remove:** `handle_read_datapoint_event()` method (line ~33-41)
- **Keep:** `SendActionEvent` and `SendWriteConfigEvent` handlers unchanged

**Reasoning:** `TelegramDebounceService` now handles `ReadDatapointFromProtocolEvent`

### Step 3: Update Dependency Injection

**File:** `src/xp/container.py`

**Add Provider:**
```python
from xp.services.protocol.telegram_debounce_service import TelegramDebounceService

@providers.singleton
def provide_telegram_debounce_service(
    event_bus: EventBus = Provide[Container.event_bus],
    telegram_protocol: TelegramProtocol = Provide[Container.telegram_protocol],
) -> TelegramDebounceService:
    return TelegramDebounceService(
        event_bus=event_bus,
        telegram_protocol=telegram_protocol,
        debounce_ms=50,
    )
```

**Update Container Class:**
```python
class Container(containers.DeclarativeContainer):
    # ... existing providers ...
    telegram_debounce_service = providers.Singleton(provide_telegram_debounce_service)
```

**IMPORTANT:** Ensure `telegram_debounce_service` is initialized BEFORE `homekit_conbus_service` in startup sequence.

### Step 4: Update Service Initialization

**File:** Check where services are initialized (likely `src/xp/services/homekit/homekit_service.py` or main entry point)

**Add:**
```python
# Ensure debounce service is created before conbus service
debounce_service = container.telegram_debounce_service()
conbus_service = container.homekit_conbus_service()
```

### Step 5: Write Unit Tests

**File:** `tests/unit/test_services/test_telegram_debounce_service.py`

**Required Tests:**

```python
class TestTelegramDebounceService:

    def test_single_request_sent_immediately(self):
        """Single request sends telegram after debounce window"""
        # Given: 1 request queued
        # When: debounce window expires
        # Then: 1 telegram sent

    def test_duplicate_requests_deduplicated(self):
        """Multiple identical requests result in single telegram"""
        # Given: 4 requests with same serial + datapoint_type
        # When: debounce window expires
        # Then: 1 telegram sent, 3 deduplicated

    def test_different_datapoints_not_deduplicated(self):
        """OUTPUT_STATE and LIGHT_LEVEL both sent"""
        # Given: 2 requests, same serial, different datapoint_type
        # When: debounce window expires
        # Then: 2 telegrams sent

    def test_different_serials_not_deduplicated(self):
        """Same datapoint for different modules both sent"""
        # Given: 2 requests, different serial, same datapoint_type
        # When: debounce window expires
        # Then: 2 telegrams sent

    @pytest.mark.asyncio
    async def test_debounce_window_batching(self):
        """Requests within window are batched"""
        # Given: Request 1 at t=0ms
        # Given: Request 2 at t=10ms (resets timer)
        # Given: Request 3 at t=20ms (resets timer)
        # When: t=70ms (50ms after last request)
        # Then: All processed in single batch

    def test_dedup_key_format(self):
        """Verify dedup key format"""
        # Given: serial="012345678901", datapoint=OUTPUT_STATE(12)
        # Then: dedup_key == "012345678901:12"
```

**Test Helpers:**
- Use `unittest.mock` for `TelegramProtocol.sendFrame()`
- Use `pytest.mark.asyncio` for async tests
- Mock `asyncio.get_event_loop().call_later()` or use fake time

### Step 6: Write Integration Tests

**File:** `tests/integration/test_debounce_integration.py`

**Required Tests:**

```python
def test_multiple_accessories_single_module(self):
    """
    4 accessories on module 012345678901
    Button press triggers 1 telegram (not 4)
    """
    # Given: 4 accessories configured with same serial_number
    # When: ModuleStateChangedEvent dispatched
    # Then: 1 telegram sent: S012345678901F02D12

def test_mixed_modules_preserved(self):
    """
    Accessories on different modules send separate telegrams
    """
    # Given: 2 accessories on module A, 2 on module B
    # When: Event affects both modules
    # Then: 2 telegrams sent (one per module)
```

### Step 7: Add Logging and Observability

**In `_process_queue()` method:**

```python
async def _process_queue(self) -> None:
    total_requests = sum(len(events) for events in self.request_queue.values())
    unique_telegrams = len(self.request_queue)
    deduped = total_requests - unique_telegrams

    self.logger.info(
        f"Debounce batch: {unique_telegrams} sent, "
        f"{deduped} deduplicated "
        f"({(deduped/total_requests)*100:.1f}% reduction)"
    )
```

### Step 8: Update Imports

Ensure all files import new service:

**Check these files:**
- `src/xp/services/__init__.py` - Add export
- `src/xp/services/protocol/__init__.py` - Add export

## Validation Checklist

Before marking complete, verify:

- [ ] `TelegramDebounceService` created with all required methods
- [ ] Service subscribes to `ReadDatapointFromProtocolEvent`
- [ ] Dedup key format: `"{serial}:{datapoint_value}"`
- [ ] Timer resets on each new request
- [ ] Queue clears after processing
- [ ] `HomeKitConbusService.handle_read_datapoint_event()` removed
- [ ] Dependency injection configured correctly
- [ ] Service initialization order correct (debounce before conbus)
- [ ] 6 unit tests written and passing
- [ ] 2 integration tests written and passing
- [ ] Logging includes dedup statistics
- [ ] `SendActionEvent` still works (not debounced)
- [ ] `SendWriteConfigEvent` still works (not debounced)

## Testing the Feature

### Manual Test

```bash
# Start service
xp homekit start

# Monitor logs for:
# "Debounce batch: X sent, Y deduplicated"

# Trigger physical button press on module with 4 accessories
# Expected: 1 telegram sent (not 4)
```

### Expected Log Output

```
DEBUG: Queued request: 012345678901:12 (queue size: 1)
DEBUG: Queued request: 012345678901:12 (queue size: 2)
DEBUG: Queued request: 012345678901:12 (queue size: 3)
DEBUG: Queued request: 012345678901:12 (queue size: 4)
INFO:  Processing queue: 1 unique, 4 total requests
DEBUG: Sending telegram for 012345678901:12 (consolidating 4 duplicates)
INFO:  Debounce batch: 1 sent, 3 deduplicated (75.0% reduction)
```

## Common Pitfalls to Avoid

1. **Don't debounce action telegrams** - Only `ReadDatapointFromProtocolEvent`
2. **Timer must reset** - Each new request extends the window
3. **Use first event** - All events in dedup list are identical
4. **Async timer** - Use `call_later()` not `sleep()`
5. **Clear queue** - Must clear after processing to prevent memory leak
6. **Service order** - Debounce must init before conbus service

## Files Modified/Created

**Created:**
- `src/xp/services/protocol/telegram_debounce_service.py`
- `tests/unit/test_services/test_telegram_debounce_service.py`
- `tests/integration/test_debounce_integration.py`

**Modified:**
- `src/xp/services/homekit/homekit_conbus_service.py`
- `src/xp/container.py`
- `src/xp/services/__init__.py` (exports)
- `src/xp/services/protocol/__init__.py` (exports)

## Success Criteria

- ✅ 4 accessories on same module → 1 telegram sent
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ No regression in existing functionality
- ✅ Logs show deduplication statistics
- ✅ 75% reduction in bus traffic for typical scenarios

## References

- Full spec: `doc/architecture/Feat-Bus-Debounce.md`
- Cache flow: `doc/architecture/Feat-Cache-Management.md`
- Existing protocol service: `src/xp/services/homekit/homekit_conbus_service.py`
- Telegram protocol: `src/xp/services/protocol/telegram_protocol.py`
