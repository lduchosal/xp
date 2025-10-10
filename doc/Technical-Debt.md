# Technical Debt

Known technical debt and design inconsistencies that should be addressed.

---

## Naming: EventTelegram.input_number → output_number

**Priority:** Medium

### Problem
`EventTelegram.input_number` and `ModuleStateChangedEvent.input_number` are misleading. The protocol format `<E12L01I08MAK>` uses `I08` where the number represents the **output/channel number** (0-9), not an input number.

### Solution
Rename to `output_number` in:
- `EventTelegram` model
- `ModuleStateChangedEvent` event
- `telegram_service.parse_event_telegram()`
- All consuming code and tests

### Impact
Breaking change - requires coordinated update across 7+ files.

---

## Parsing: EventTelegram output_number not normalized

**Priority:** Medium

### Problem
Event telegram `<E12L01I82MAK>` is parsed with `output_number=82`, but should be normalized to `output_number=2`. The protocol uses `I80-I89` to represent outputs 0-9, but `EventTelegram` should store the logical output number (0-9), not the raw protocol value (80-89).

### Solution
Update `telegram_service.parse_event_telegram()` to normalize:
- `I80 → output_number=0`
- `I81 → output_number=1`
- `I82 → output_number=2`
- etc.

### Impact
Breaking change - affects event handling and cache refresh logic.

---

*Add additional technical debt items below as they are identified.*
