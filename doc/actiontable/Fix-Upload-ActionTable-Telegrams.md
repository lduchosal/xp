# Upload ActionTable - Telegram Validation

This document provides the expected telegram sequence for uploading a complete 96-entry action table, used for validating the upload implementation.

## Purpose

This serves as a specification for integration tests that verify:
1. **96-entry padding**: ActionTable is correctly padded to exactly 96 entries
2. **Chunk sequencing**: Data is chunked into 64-character segments
3. **Prefix sequence**: Each chunk telegram has the correct sequential prefix (AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ, AK, AL, AM, AN, AO)
4. **Complete data integrity**: The full serialized action table is transmitted correctly

## Test Requirements

### Unit Test: `test_upload_generates_correct_telegrams`

**Objective**: Given a complete ActionTable, verify that the upload service generates the correct sequence of ACTIONTABLE telegrams with proper chunk prefixes.

**Setup**:
- Create ActionTable with 96 NOMOD entries (or any valid configuration)
- Mock the conson config with the action table
- Mock the telegram sending to capture generated telegrams

**Verification**:
- Exactly 15 ACTIONTABLE telegrams are generated (960 chars / 64 chars per chunk)
- Telegram prefixes follow sequence: AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ, AK, AL, AM, AN, AO
- Each telegram data_value starts with correct prefix
- Combined chunk data matches serialized action table output
- EOF telegram is sent after all chunks

## Test Implementation

### Test Location
`tests/unit/test_services/test_actiontable_upload_service.py`

### Test Pseudocode

```python
def test_upload_generates_correct_telegram_sequence(self):
    """Test that full ActionTable upload generates correct telegram sequence."""
    # Setup: Create 96-entry NOMOD action table
    action_table = ActionTable(entries=[...])  # 96 NOMOD entries

    # Setup: Mock conson config
    mock_module = Mock()
    mock_module.action_table = [...]  # String representations
    mock_conson_config.find_module.return_value = mock_module

    # Setup: Mock serializer
    serializer.from_short_string.return_value = action_table
    serializer.to_encoded_string.return_value = "AAA...AAA"  # 960 chars

    # Setup: Capture all send_telegram calls
    sent_telegrams = []

    def capture_telegram(**kwargs):
        sent_telegrams.append(kwargs)

    with patch.object(service, 'send_telegram', side_effect=capture_telegram):
        # Start upload and simulate ACK responses
        service.init(serial_number="0020044974", ...)

        # Simulate connection established
        service.connection_established()

        # Simulate ACK responses for each chunk
        mock_ack = Mock(system_function=SystemFunction.ACK)
        for _ in range(15):  # 15 chunks expected
            service._handle_upload_response(mock_ack)

    # Verify: Exactly 16 telegrams sent (1 UPLOAD_ACTIONTABLE + 15 ACTIONTABLE)
    assert len(sent_telegrams) == 16

    # Verify: First telegram is UPLOAD_ACTIONTABLE
    assert sent_telegrams[0]['system_function'] == SystemFunction.UPLOAD_ACTIONTABLE

    # Verify: Next 15 telegrams are ACTIONTABLE with correct prefixes
    expected_prefixes = ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH',
                         'AI', 'AJ', 'AK', 'AL', 'AM', 'AN', 'AO']

    for i, expected_prefix in enumerate(expected_prefixes):
        telegram = sent_telegrams[i + 1]
        assert telegram['system_function'] == SystemFunction.ACTIONTABLE
        assert telegram['data_value'].startswith(expected_prefix)
        assert len(telegram['data_value']) == 66  # 2-char prefix + 64-char chunk

    # Verify: Last telegram is EOF
    assert sent_telegrams[-1]['system_function'] == SystemFunction.EOF
```

### Additional Assertions

1. **Data Integrity**: Concatenate all chunk data (excluding prefixes) and verify it matches `serializer.to_encoded_string()` output
2. **Chunk Size**: Each chunk (excluding prefix) should be exactly 64 characters except possibly the last
3. **Prefix Formula**: Verify each prefix matches `0xA0 | (0xA + chunk_index)` formula
4. **Serial Number**: All telegrams use the correct serial number

## Example: Full NOMOD Action Table

Serial Number: `0020044974`

## Expected Telegrams

### Telegram Structure Breakdown

Each ACTIONTABLE telegram follows this format:
```
<S{serial}F17D{prefix}{chunk_data}{checksum}>
```

Where:
- `S{serial}`: System telegram for specified serial number
- `F17D`: System function code for ACTIONTABLE
- `{prefix}`: Two-character hex prefix (AA, AB, AC, etc.)
- `{chunk_data}`: 64 characters of action table data in hex nibbles
- `{checksum}`: Two-character checksum

### Full Telegram Sequence

**Note**: Prefix sequence is AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ, AK, AL, AM, AN, AO (15 telegrams for 960 total characters)

```
<S0020044974F17DAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFO>
<S0020044974F17DAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFN>
<S0020044974F17DAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFM>
<S0020044974F17DAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFL>
<S0020044974F17DAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFK>
<S0020044974F17DAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFJ>
<S0020044974F17DAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFI>
<S0020044974F17DAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFH>
<S0020044974F17DAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFG>
<S0020044974F17DAAAJAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFF>
<S0020044974F17DAAAKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFE>
<S0020044974F17DAAALAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>
<S0020044974F17DAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFC>
<S0020044974F17DAAANAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFB>
<S0020044974F17DAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>
```

### Prefix Verification

| Chunk # | Prefix | Formula                       | Telegram Extract |
|---------|--------|-------------------------------|------------------|
| 0 | AAAA | AA + 0xA0 \| (0xA + 0) = 0xAA | `F17DAAAA...`    |
| 1 | AAAB | AA + 0xA0 \| (0xA + 1) = 0xAB      | `F17DAAAB...`      |
| 2 | AAAC | AA + 0xA0 \| (0xA + 2) = 0xAC      | `F17DAAAC...`      |
| 3 | AAAD | AA + 0xA0 \| (0xA + 3) = 0xAD      | `F17DAAAD...`      |
| 4 | AAAE | AA + 0xA0 \| (0xA + 4) = 0xAE      | `F17DAAAE...`      |
| 5 | AAAF | AA + 0xA0 \| (0xA + 5) = 0xAF      | `F17DAAAF...`      |
| 6 | AAAG | AA + 0xA0 \| (0xA + 6) = 0xB0      | `F17DAAAG...`      |
| 7 | AAAH | AA + 0xA0 \| (0xA + 7) = 0xB1      | `F17DAAAH...`      |
| 8 | AAAI | AA + 0xA0 \| (0xA + 8) = 0xB2      | `F17DAAAI...`      |
| 9 | AAAJ | AA + 0xA0 \| (0xA + 9) = 0xB3      | `F17DAAAJ...`      |
| 10 | AAAK | AA + 0xA0 \| (0xA + 10) = 0xB4     | `F17DAAAK...`      |
| 11 | AAAL | AA + 0xA0 \| (0xA + 11) = 0xB5     | `F17DAAAL...`      |
| 12 | AAAM | AA + 0xA0 \| (0xA + 12) = 0xB6     | `F17DAAAM...`      |
| 13 | AAAN | AA + 0xA0 \| (0xA + 13) = 0xB7     | `F17DAAAN...`      |
| 14 | AAAO | AA + 0xA0 \| (0xA + 14) = 0xB8     | `F17DAAAO...`      |

## ActionTable
```
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID;
NOMOD 0 0 > 0 VOID
```

## Summary

This specification ensures that the ActionTable upload implementation correctly:

1. **Pads to 96 entries**: Always sends exactly 480 bytes (96 entries × 5 bytes each)
2. **Chunks correctly**: Divides encoded data into 64-character chunks
3. **Sequences prefixes**: Uses sequential AA, AB, AC... AO prefixes (15 chunks for full table)
4. **Maintains integrity**: Complete data can be reconstructed from received chunks

### Key Metrics
- **Total entries**: 96 (padded with NOMOD if necessary)
- **Total bytes**: 480 (96 × 5)
- **Encoded length**: 960 hex characters (480 × 2)
- **Chunk size**: 64 characters
- **Number of chunks**: 15 (960 ÷ 64)
- **Prefix sequence**: AA through AO (15 values)

### Integration Test Success Criteria
✓ Upload service generates exactly 15 ACTIONTABLE telegrams
✓ Each telegram has correct sequential prefix (AA-AO)
✓ Combined chunk data totals 960 characters
✓ Concatenated chunks match serializer output
✓ EOF telegram sent after final chunk

