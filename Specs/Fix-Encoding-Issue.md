# Fix Encoding Issue

## Problem Description

The application encounters UTF-8 decoding errors when receiving responses from conbus devices. The conbus protocol uses Latin-1 messaging, and some device responses contain extended characters (bytes > 127) that cannot be decoded as UTF-8.

### Error Details

**Error Message:**
```
Error receiving responses: 'utf-8' codec can't decode byte 0xa7 in position 23: invalid start byte
```

**Analysis:**
- The conbus protocol uses Latin-1 text format: `<S...>` for sent messages, `<R...>` for responses
- Byte 0xa7 (167 decimal) = § symbol in Latin-1/ISO-8859-1 encoding
- This byte is not valid UTF-8

**Raw Data Analysis:**
```
Sent message:
Hex: 3c53 3030 3230 3034 3439 3636 4630 3244 3138 4642 3e 
Latin-1: <S0020044966F02D18FB>

Problem response:
Hex: 3c52 3030 3230 3034 3439 3636 4630 3244 3138 2b33 312c 35a7 4349 453e  
Latin-1: <R0020044966F02D18+31,5§CIE>
Problem byte: 0xa7 at position 23 (§ symbol)
```

## Root Cause

The issue occurs in the `conbus_client_send_service.py` at line 266:
```python
message = data.decode('utf-8').strip()
```

The received data contains extended characters (specifically 0xa7 = § symbol) that are valid in Latin-1 but not in UTF-8. The current code assumes UTF-8 encoding, which fails on these extended characters.

## Affected Files

- `/src/xp/services/conbus_client_send_service.py:266`
- `/src/xp/services/conbus_server_service.py:135`
- `/tests/integration/test_conbus_client_send_integration.py:70`

## Proposed Solution

### Option 1: Direct Latin-1 Decoding (Recommended)
Since conbus protocol uses Latin-1 encoding:

```python
# Latin-1 can decode any byte (0-255) to Unicode
message = data.decode('latin-1').strip()
```

## Recommended Implementation

Implement **Option 1** (Direct Latin-1 decoding) because:
- Matches the actual protocol encoding
- Handles all characters consistently
- Maintains compatibility with existing message parsing
- Simplest and most reliable approach

## Testing Requirements

1. Test with normal Latin-1 messages: `<S0020044966F02D18FB>`
2. Test with extended characters: `<R0020044966F02D18+31,5§CIE>` (0xa7)
3. Test with various Latin-1 characters (128-255 range)
4. Ensure telegram parsing continues to work correctly
5. Test both sent (`<S...>`) and received (`<R...>`) message formats

## Impact Assessment

- **Low Risk**: The change adds error handling without breaking existing functionality
- **Performance**: Minimal impact, only affects error cases
- **Compatibility**: Maintains backward compatibility while handling edge cases

## Success Criteria

1. No more UTF-8 decode exceptions
2. All conbus communication continues to work
3. Extended Latin-1 characters are handled correctly
4. Test coverage includes edge cases
