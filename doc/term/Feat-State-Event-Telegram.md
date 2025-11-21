# State Event Telegram Monitoring

## Overview

This feature extends the State Monitor TUI to listen for and process output event telegrams from XP24 relay modules. When an XP24 module's output state changes, it broadcasts an event telegram that can be used to update the module state display in real-time.

## Problem Statement

Currently, the State Monitor TUI only updates module output states through explicit queries (READ_DATAPOINT requests). However, XP24 modules with auto-report enabled broadcast event telegrams whenever their output states change. These event telegrams are currently ignored by the State Monitor, resulting in:

- Stale display information between manual refreshes
- Missed real-time state changes
- Unnecessary polling overhead

## Solution

Listen for output event telegrams and use them to update the module state display automatically when outputs change.

## Event Telegram Format

Output event telegrams follow the format:
```
<[EO]{module_type}L{link_number}I{output_number}{event_type}{checksum}>
```

### XP24 Output Event Example

```
<E07L09I80MAE>
```

Breaking down this telegram:
- `E` - Event telegram type (can also be `O` for output)
- `07` - Module type code (7 = XP24 relay module)
- `L09` - Link number 09
- `I80` - Output indicator (80 = output 0)
- `M` - Event type (M = Make/ON, B = Break/OFF)
- `AE` - Checksum

### Output Number Encoding

For XP24 output event telegrams, the "input number" field is repurposed to indicate output number:
- `80` - Output 0
- `81` - Output 1
- `82` - Output 2
- `83` - Output 3

This is an overloaded use of the input_number field in the EventTelegram model.

## XP24 Module Analysis

### Module Type
- **Name**: XP24
- **Code**: 7
- **Description**: XP relay module
- **Outputs**: 4 relay outputs (0-3)

### Auto-Report Behavior

When auto-report is enabled (`auto_report_status == "PP"`), the XP24 module broadcasts event telegrams whenever an output state changes, either:
1. In response to an action request (after ACK telegram)
2. Due to internal action table execution
3. From external inputs or time-based actions

### Event Generation

XP24 generates output event telegrams when:
- An output is turned ON (Make event: `M`)
- An output is turned OFF (Break event: `B`)

Example sequence for turning output 0 ON:
1. System telegram: `<S{serial}F42D00AB{checksum}>` (action request)
2. ACK response: `<R{serial}F40D{checksum}>`
3. Event telegram: `<E07L{link}I80M{checksum}>` (if auto-report enabled)

## Implementation Plan

### 1. Event Telegram Processing

Extend `StateMonitorService._on_telegram_received()` to handle event telegrams in addition to reply telegrams. The method should check the telegram type and route to appropriate handlers.

### 2. Event Telegram Handler

Create handler for event telegrams that:
- Parses the event telegram using TelegramService
- Filters for XP24 output events only (module_type == 7)
- Validates output number range (80-83 for outputs 0-3)
- Finds the corresponding module by link number
- Updates the output state in the module's outputs field
- Updates the last_update timestamp
- Emits module_state_changed signal

### 3. Module Lookup by Link Number

Implement helper method to find module state by link number, as current lookup is by serial number only.

### 4. Output State Update

Implement method to update individual output bits in the module state's outputs string (format: "0 1 0 0"). The method should:
- Parse the space-separated outputs string
- Update the specific output bit at the given position
- Handle cases where outputs string is empty or too short
- Convert back to space-separated string format

## Testing Strategy

### Unit Tests

1. Test event telegram parsing for XP24 outputs
2. Test module lookup by link number
3. Test output bit update logic
4. Test event handler ignores non-XP24 events
5. Test event handler ignores non-output events (input_number < 80)

### Integration Tests

1. Connect to XP24 emulator with auto-report enabled
2. Send action requests to change output states
3. Verify event telegrams are received
4. Verify module state display updates automatically
5. Test multiple outputs changing in sequence
6. Test multiple XP24 modules with different link numbers

### Manual Testing

1. Start State Monitor TUI
2. Connect to XP24 device with auto-report enabled
3. Trigger output changes via:
   - External action requests
   - Action table events
   - Physical inputs (if available)
4. Observe real-time updates in the TUI

## Edge Cases

1. **Event telegram without matching link number**: Ignore silently
2. **Input event telegram (I00-I09)**: Ignore (not an output event)
3. **Non-XP24 event telegram**: Ignore (only XP24 supported initially)
4. **Malformed event telegram**: Log error, ignore
5. **Event for unknown output number**: Log warning, ignore
6. **Module without auto-report**: No events generated (expected)

## Future Enhancements

1. **Support other module types**: Extend to XP33, XP33LR, XP33LED output events
2. **Event statistics**: Track event counts and last event time
3. **Event filtering**: Option to disable event-based updates
4. **Event log**: Display recent events in TUI
5. **Conflict resolution**: Handle case where event and query responses conflict

## Related Documents

- `doc/telegram/Feat-Telegram-Event.md` - Event telegram specification
- `doc/modules/Feat-Module-Type.md` - Module type codes
- `doc/term/Feat-Module-State.md` - Module state TUI specification
- `src/xp/models/telegram/event_telegram.py` - EventTelegram model
- `src/xp/services/server/xp24_server_service.py` - XP24 emulator implementation

## Notes

- The EventTelegram model currently uses `input_number` for both inputs and outputs
- For XP24 output events, `input_number` values 80-83 represent outputs 0-3
- This is an implementation detail of the XP24 firmware
- The `event_telegram_type` field distinguishes `E` vs `O` telegram types (both are event telegrams)
- Auto-report must be enabled for event telegrams to be broadcast
