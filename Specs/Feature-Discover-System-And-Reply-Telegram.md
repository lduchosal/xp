# Conson Bus Discovery Telegram Specification

## Discovery Request

**Format:** `<S0000000000F01D00FA>`

| Field | Position | Length | Value | Description |
|-------|----------|--------|-------|-------------|
| Start | 0 | 1 | S | Send command indicator |
| Source Address | 1-10 | 10 | 0000000000 | Master/broadcast source (all zeros) |
| Command | 11-16 | 6 | F01D00 | Discovery command |
| Checksum | 17-18 | 2 | FA | Message integrity check |

### Command Details
- **F01D00**: Discovery command to enumerate all connected devices
- Broadcast message (source address all zeros indicates broadcast)
- All devices on the bus must respond if operational

## Device Response

**Format:** `<R[10-digit-serial]F01D[checksum]>`

| Field | Position | Length | Description |
|-------|----------|--------|-------------|
| Start | 0 | 1 | R = Response indicator |
| Serial Number | 1-10 | 10 | Unique device serial number |
| Ack Command | 11-16 | 6 | F01D + calculated suffix |
| Checksum | 17 | 1 | Single character checksum |

### Response Examples
```
<R0020030837F01DFM>  // Serial: 0020030837
<R0020044966F01DFK>  // Serial: 0020044966
<R0020042796F01DFN>  // Serial: 0020042796
```
### Sample files
- Specs/ConbusLog.txt
- Specs/ConbusLog-discover.txt


### Response Rules
1. Each device responds with its unique 10-digit serial number
2. Response format: F01D + single checksum character
3. Devices must respond within the bus timeout window
4. Serial numbers are factory-assigned and immutable

## Protocol Behavior
- **Master** sends discovery broadcast
- **All devices** respond with their serial identification
- **Master** compiles device inventory from responses
- Used for network topology mapping and device enumeration

## Error Handling
- Non-responsive devices are considered offline
- Duplicate serial numbers indicate hardware defect or bus error
- Malformed responses should be logged and ignored