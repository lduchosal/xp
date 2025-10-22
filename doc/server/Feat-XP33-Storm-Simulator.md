# XP33 Storm Mode Simulator

## Overview
Simulates XP33LR "dead loop" storm behavior for testing Bus Error Management Service. When triggered, emulator sends thousands of duplicate telegrams, mimicking real-world firmware failure mode.

## Storm Behavior

### Normal Operation
- Responds to queries with single telegram
- Processes incoming requests normally
- MODULE_ERROR_CODE (datapoint 10) returns `00` (normal)

### Storm Mode Activated
- Sends **100-500 identical response telegrams** for single query
- Continues storm until MODULE_ERROR_CODE query received
- MODULE_ERROR_CODE returns `FE` (buffer overflow) or `FF` (fatal error)
- All other datapoint queries ignored during storm

### Recovery
- MODULE_ERROR_CODE query immediately stops storm
- Returns to normal operation after error query response
- Subsequent MODULE_ERROR_CODE queries return `00` (normal)

## Trigger Conditions

### Automatic Triggers (Configurable)
1. **Query Burst**: Receive ≥10 query telegrams within 100ms window
2. **Repeated Queries**: Same datapoint queried ≥5 times within 1 second
3. **Action Overload**: Receive ≥3 action telegrams within 50ms

### Manual Trigger
- Datapoint query to special value: `D99` (test trigger)
- Immediately enters storm mode

## Configuration

```yaml
# server.yml
devices:
  0012345003:
    type: XP33
    storm_simulation:
      enabled: true

      # Trigger thresholds
      trigger_query_burst_count: 10      # Queries in window
      trigger_query_burst_window_ms: 100 # Time window
      trigger_repeated_query_count: 5    # Same datapoint
      trigger_repeated_query_window_ms: 1000

      # Storm behavior
      storm_telegram_count: 200          # Telegrams per storm
      storm_telegram_interval_ms: 1      # Delay between telegrams
      storm_error_code: "FE"             # Error code during storm (FE or FF)

      # Recovery
      auto_recovery_enabled: false       # Auto-stop after N telegrams
      auto_recovery_telegram_count: 1000 # Max telegrams before auto-stop
```

## Implementation

### State Machine
```
NORMAL ──[trigger]──> STORM ──[error query]──> NORMAL
  │                      │
  └───[D99 query]────────┘
```

### Response Logic

**Normal State:**
```python
if datapoint == "10":  # MODULE_ERROR_CODE
    return "R{serial}F02D1000FP"  # 00 = normal
elif datapoint == "99":  # Test trigger
    enter_storm_mode()
    return None  # No response, storm starts
else:
    return normal_response(datapoint)
```

**Storm State:**
```python
if datapoint == "10":  # MODULE_ERROR_CODE
    send_response("R{serial}F02D10{error_code}FP")
    exit_storm_mode()
else:
    # Ignore query, continue storm
    for i in range(storm_telegram_count):
        send_response(last_response)  # Repeat last telegram
        await asyncio.sleep(storm_interval_ms / 1000)
```

### Trigger Detection

```python
class StormTriggerDetector:
    def __init__(self, config):
        self.query_history = []
        self.config = config

    def should_trigger_storm(self, telegram):
        """Check if telegram should trigger storm mode"""
        now = time.time()

        # Add to history
        self.query_history.append({
            'timestamp': now,
            'datapoint': extract_datapoint(telegram)
        })

        # Clean old entries
        cutoff = now - (self.config.trigger_query_burst_window_ms / 1000)
        self.query_history = [
            q for q in self.query_history
            if q['timestamp'] > cutoff
        ]

        # Check query burst threshold
        if len(self.query_history) >= self.config.trigger_query_burst_count:
            return True

        # Check repeated query threshold
        datapoint = extract_datapoint(telegram)
        repeated_count = sum(
            1 for q in self.query_history
            if q['datapoint'] == datapoint
        )
        if repeated_count >= self.config.trigger_repeated_query_count:
            return True

        return False
```

## Testing

### Manual Test Sequence
```bash
# 1. Start server with storm simulation enabled
xp server start

# 2. Trigger storm via special datapoint
echo "<S0012345003F02D99FX>" | nc localhost 10001

# 3. Observe storm (should receive hundreds of telegrams)

# 4. Stop storm with error query
echo "<S0012345003F02D10FO>" | nc localhost 10001

# 5. Verify normal operation resumed
echo "<S0012345003F02D12FM>" | nc localhost 10001
```

### Automated Test Cases
1. **Storm Trigger**: Verify burst threshold triggers storm
2. **Storm Telegram Count**: Verify correct number of duplicate telegrams
3. **Error Code**: Verify MODULE_ERROR_CODE returns FE/FF during storm
4. **Recovery**: Verify error query stops storm immediately
5. **Post-Recovery**: Verify normal status after recovery

## Integration with Bus Error Management

### Expected Behavior
1. Client sends query burst → Storm triggered
2. Server detects high telegram rate → Sends MODULE_ERROR_CODE query
3. Emulator receives error query → Stops storm, returns error code
4. Client detects recovery → System returns to normal

### Metrics to Validate
- Storm detection latency: <500ms
- Storm recovery time: <100ms after error query
- False positive rate: 0% (no storms during normal operation)

## Error Codes

| Code | State | Description |
|------|-------|-------------|
| `00` | Normal | Module operating normally |
| `FE` | Storm | Internal buffer overflow (simulated dead loop) |
| `FF` | Storm | Fatal error (simulated dead loop) |

## Logging

```
INFO: Storm simulation enabled for device 0012345003
WARN: Storm triggered: query burst detected (12 queries in 95ms)
INFO: Entering storm mode, sending 200 duplicate telegrams
WARN: Storm active: sent 45/200 telegrams
INFO: MODULE_ERROR_CODE query received, stopping storm
INFO: Storm stopped, returning to normal operation
```

## References
- **Bus Error Management**: `doc/architecture/Feat-Bus-Error-Management.md`
- **XP33 Emulator**: `doc/server/Feat-XP33-Emulator-Spec.md`
- **Datapoint Types**: `src/xp/models/telegram/datapoint_type.py`