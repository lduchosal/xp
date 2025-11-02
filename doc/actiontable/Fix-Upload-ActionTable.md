# Fix Upload ActionTable

This document describes fixes needed for the ActionTable upload implementation.

## Background

The ActionTable upload feature was implemented to upload actiontable configurations from `conson.yml` to XP module flash memory. The implementation has two critical bugs that prevent correct operation.

## Related Documentation

See `Feat-Upload-ActionTable.md` for the original feature specification and implementation plan.

## Current Implementation Issues

### 1. Missing 96 Entries Padding

**Problem:**
The ActionTable serializer (`src/xp/services/actiontable/actiontable_serializer.py:89`) does not pad the action table to 96 entries when serializing for upload.

**Current Behavior:**
```python
def to_data(action_table: ActionTable) -> bytes:
    """Serialize ActionTable to telegram byte data."""
    data = bytearray()

    for entry in action_table.entries:
        # Encode each entry as 5 bytes
        # ...
        data.extend([type_byte, link_byte, input_byte, output_command_byte, parameter_byte])

    return bytes(data)
```

If the action table has 8 entries, only 8×5 = 40 bytes are serialized.

**Expected Behavior:**
ActionTables must always contain exactly 96 entries. If fewer entries are configured, the remaining slots must be filled with default entries: `NOMOD 0 0 > 0 TURNOFF` (encoded as `00 00 00 00 00`).

**Impact:**
- Module expects exactly 96 entries (480 bytes) of action table data
- Uploading fewer entries may cause undefined behavior or corruption
- Flash memory structure requires fixed-size table

**Location:** `src/xp/services/actiontable/actiontable_serializer.py:89-117`

### 2. Incorrect Telegram Chunk Prefix

**Problem:**
The upload service (`src/xp/services/conbus/actiontable/actiontable_upload_service.py:113`) prefixes all ACTIONTABLE telegrams with `"00"` regardless of chunk index.

**Current Behavior:**
```python
self.send_telegram(
    telegram_type=TelegramType.SYSTEM,
    serial_number=self.serial_number,
    system_function=SystemFunction.ACTIONTABLE,
    data_value=f"00{chunk}",  # Always "00" prefix
)
```

**Expected Behavior:**
Each ACTIONTABLE telegram should be prefixed with a sequence counter that increments with each chunk:
- First chunk: `AA` prefix → `AA{chunk_data}`
- Second chunk: `AB` prefix → `AB{chunk_data}`
- Third chunk: `AC` prefix → `AC{chunk_data}`
- Fourth chunk: `AD` prefix → `AD{chunk_data}`
- etc.

The prefix consists of:
- High nibble (A): Indicates this is an ACTIONTABLE data telegram
- Low nibble (A,B,C,D...): Sequential chunk counter starting from A (0xA = 10)

**Impact:**
- Module cannot track which chunks it has received
- Upload may fail or result in corrupted action table
- Module may reject telegrams with incorrect sequence numbers

**Location:** `src/xp/services/conbus/actiontable/actiontable_upload_service.py:113`

## Fix Implementation

### Fix 1: Pad to 96 Entries

**Approach:**
Modify `ActionTableSerializer.to_data()` to always pad to 96 entries.

**Pseudocode:**
```python
def to_data(action_table: ActionTable) -> bytes:
    data = bytearray()

    # Serialize actual entries
    for entry in action_table.entries:
        # ... existing encoding logic ...
        data.extend([type_byte, link_byte, input_byte, output_command_byte, parameter_byte])

    # Pad to 96 entries with default NOMOD entries
    MAX_ENTRIES = 96
    current_entries = len(action_table.entries)

    if current_entries < MAX_ENTRIES:
        padding_bytes = [0x00, 0x00, 0x00, 0x00, 0x00]  # NOMOD default entry
        for _ in range(MAX_ENTRIES - current_entries):
            data.extend(padding_bytes)

    return bytes(data)
```

**Default Entry Encoding:**
- `module_type`: `NOMOD` (0x00)
- `link_number`: 0 (0x00)
- `module_input`: 0 (0x00)
- `module_output`: 0, `command`: `TURNOFF` (0) → (0x00)
- `parameter`: 0 (0x00)

### Fix 2: Correct Chunk Prefix

**Approach:**
Modify `ActionTableUploadService._handle_upload_response()` to use sequential chunk counter.

**Pseudocode:**
```python
def _handle_upload_response(self, reply_telegram: Any) -> None:
    if reply_telegram.system_function == SystemFunction.ACK:
        if self.current_chunk_index < len(self.upload_data_chunks):
            chunk = self.upload_data_chunks[self.current_chunk_index]

            # Calculate prefix: 0xAA, 0xAB, 0xAC, 0xAD, ...
            # High nibble = 0xA (constant)
            # Low nibble = 0xA + chunk_index (0xA, 0xB, 0xC, 0xD, ...)
            prefix_value = 0xA0 | (0xA + self.current_chunk_index)
            prefix_hex = f"{prefix_value:02X}"

            self.send_telegram(
                telegram_type=TelegramType.SYSTEM,
                serial_number=self.serial_number,
                system_function=SystemFunction.ACTIONTABLE,
                data_value=f"{prefix_hex}{chunk}",
            )
            self.current_chunk_index += 1
```

**Prefix Sequence:**
```
Chunk 0: AA (0xA0 | 0xA = 0xAA)
Chunk 1: AB (0xA0 | 0xB = 0xAB)
Chunk 2: AC (0xA0 | 0xC = 0xAC)
Chunk 3: AD (0xA0 | 0xD = 0xAD)
...
Chunk 15: BJ (if needed - wraps to next high nibble)
```

## Testing Requirements

### Test Case 1: Verify 96 Entry Padding

**Setup:**
- Create action table with 8 entries
- Serialize to bytes

**Assertions:**
- Output length = 480 bytes (96 entries × 5 bytes)
- First 40 bytes contain actual entries
- Remaining 440 bytes are all zeros (default NOMOD entries)

### Test Case 2: Verify Chunk Prefix Sequence

**Setup:**
- Create action table requiring 4 chunks
- Mock upload responses

**Assertions:**
- First ACTIONTABLE telegram starts with `AA`
- Second ACTIONTABLE telegram starts with `AB`
- Third ACTIONTABLE telegram starts with `AC`
- Fourth ACTIONTABLE telegram starts with `AD`

### Test Case 3: End-to-End Upload

**Setup:**
- Configure module with action table in conson.yml
- Run `xp conbus actiontable upload <serial>`

**Assertions:**
- Upload completes successfully
- Module flash contains exactly 96 entries
- Download action table matches uploaded configuration

## Implementation Priority

1. **High Priority - Fix 1 (Padding)**: Critical for protocol compliance
2. **High Priority - Fix 2 (Prefix)**: Critical for reliable multi-chunk uploads
3. **Required Testing**: Both unit and integration tests

## Quality Gates

Run quality checks after implementing fixes:
```bash
sh publish.sh --quality
```

All checks must pass before considering the fix complete.