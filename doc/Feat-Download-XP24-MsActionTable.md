# XP24 MS Action Table Download Feature

XP24 module's action table can be programmed into the module flash memory. This feature enables downloading and uploading action tables that define how inputs respond to events.

## CLI Usage

### Download Action Table
```bash
xp conbus msactiontable download <serial_number> [decode (default true)]
```

### Example Output

```json
{
  "serial_number": "0123450001",
  "action_table": {
    "input1_action": {
      "type": "TOGGLE",
      "param": null
    },
    "input2_action": {
      "type": "TOGGLE",
      "param": null
    },
    "input3_action": {
      "type": "TOGGLE",
      "param": null
    },
    "input4_action": {
      "type": "TOGGLE",
      "param": null
    },
    "mutex12": false,
    "mutex34": false,
    "curtain12": false,
    "curtain34": false,
    "ms": 12
  },
  "raw": "AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
}
```

## Protocol Communication

### Download Sequence
```
[TX] <S0123450001F13D00FK>   DOWNLOAD MS ACTION TABLE REQUEST
[RX] <R0123450001F18DFA>     ACK
[RX] <R0123450001F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>   TABLE DATA
[TX] <S0123450001F18D00FB>   CONTINUE
[RX] <R0123450001F16DFO>     EOF
```

### Telegram Format

#### MS Action Table Query (F13)
```
<S{serial}F13D00{checksum}>
```

#### MS Action Table Response (F17)
```
<S{serial}F17DAAAA{4_rows}{mutex12}{mutex34}{ms}{curtain12}{curtain34}{padding}{checksum}>
```

Where:
- `{4_rows}`: 8 bytes (4 rows × 2 bytes per row: function_id + parameter_id)
- `{mutex12}`: AA/AB (mutex for inputs 1-2)
- `{mutex34}`: AA/AB (mutex for inputs 3-4)
- `{ms}`: Timing value (MS300=12, MS500=20)
- `{curtain12}`: AA/AB (curtain setting for inputs 1-2)
- `{curtain34}`: AA/AB (curtain setting for inputs 3-4)
- `{padding}`: 19 bytes of "AA" padding

## Python Implementation

see Feat-Download-XP24-MsActionTable.pseudo.md