# XP33 Storm Mode Simulator

## Overview
Simulates XP33LR "dead loop" storm behavior for testing Bus Error Management Service. When triggered, emulator sends 200 duplicate telegrams, mimicking real-world firmware failure mode.

## Storm Behavior

### Normal Operation
- Responds to queries with single telegram
- MODULE_ERROR_CODE (datapoint 10) returns `00` (normal)

### Storm Mode
- Sends **200 identical response telegrams**

### Recovery
- MODULE_ERROR_CODE query stops storm immediately
- Subsequent queries return `00` (normal)

## Trigger

**Manual trigger only**: Query datapoint `D99` to enter storm mode immediately.

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
    send_response("R{serial}F02D10FEFP")  # FE = buffer overflow
    exit_storm_mode()
else:
    # Ignore query, send storm of duplicates
    for i in range(200):  # 200 duplicate telegrams
        send_response(last_response)
        await asyncio.sleep(0.001)  # 1ms between telegrams
```

## Testing

### Test Sequence
```bash
# 1. Trigger storm via datapoint D99
echo "<S0012345003F02D99FX>" | nc localhost 10001

# 2. Observe storm (200 duplicate telegrams)

# 3. Stop storm with MODULE_ERROR_CODE query
echo "<S0012345003F02D10FO>" | nc localhost 10001
# Response: R0012345003F02D10FEFP (error code FE)

# 4. Verify normal operation resumed
echo "<S0012345003F02D10FO>" | nc localhost 10001
# Response: R0012345003F02D1000FP (error code 00)
```

## Integration with Bus Error Management

### Expected Behavior
1. Client triggers storm manually (D99 query)
2. Emulator sends 200 duplicate telegrams
3. Client sends MODULE_ERROR_CODE query
4. Storm stops, error code returned
5. System returns to normal

## Error Codes

| Code | State  | Description                                   |
|------|--------|-----------------------------------------------|
| `00` | Normal | Module operating normally                     |

## Logging

```
INFO: Storm triggered via D99 query for device 0012345003
INFO: Sending 200 duplicate telegrams
INFO: MODULE_ERROR_CODE query received, stopping storm
INFO: Storm stopped, returning to normal operation
```

## References
- **Bus Error Management**: `doc/architecture/Feat-Bus-Error-Management.md`
- **XP33 Emulator**: `doc/server/Feat-XP33-Emulator-Spec.md`
- **Datapoint Types**: `src/xp/models/telegram/datapoint_type.py`