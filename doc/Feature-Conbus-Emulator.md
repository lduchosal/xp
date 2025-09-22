# Conbus Emulator

## Overview
TCP server that emulates Conbus device behavior for testing and development purposes. Listens on port 1000 and responds to Discover Requests with configurable device information.

## TCP Server
- **Protocol**: TCP
- **Port**: 10001
- **Binding**: Listen on all interfaces (0.0.0.0:10001)
- **Connection**: Accept a single connections
- **Timeout**: 30 seconds for idle connections

## Discover Request Handling
The emulator responds to incoming Discover Request telegrams with the format:
```
<S0000000000F01D00FA>
```

### Response Format
```
<R[10-digit-serial]F01D[checksum]>
```

## Configuration File (config.yml)
The emulator reads device configurations from `config.yml`:

```yaml
devices:
  2002022202: XP20
  2410010001: XP24
```

### Configuration Rules
- **Key**: Device identifier/name (e.g., XP20, XP24)
- **Value**: 10-digit serial number string
- Multiple devices can be configured
- Each device responds individually to Discover Requests

## Protocol Behavior
1. **Listen**: TCP server accepts connections on port 10001
2. **Receive**: Parse incoming Discover Request telegram
3. **Validate**: Check telegram format and checksum
4. **Respond**: Send response for each configured device
5. **Close**: Maintain connection for additional requests

### Response Generation
For each configured device:
1. Extract serial number from config
2. Format response: `<R{serial}F01D{checksum}>`
3. Calculate checksum using standard algorithm
4. Send response immediately

## Error Handling
- **Invalid Request**: Log error, no response
- **Malformed Config**: Log error, use empty device list
- **Connection Error**: Log and continue serving other connections
- **Checksum Error**: Log invalid request, no response

## Logging
- Connection establishment/termination
- Discover requests received
- Responses sent (device serial numbers)
- Configuration file loading
- Error conditions

## Implementation Architecture

### Services
- **services/server_service.py**: Main TCP server implementation
  - Manages TCP socket lifecycle
  - Handles client connections
  - Parses Discover Request telegrams
  - Coordinates device responses
  
- **services/xp24_server_service.py**: XP24 device emulation
  - Generates XP24-specific responses
  - Handles XP24 device configuration
  - Implements XP24 telegram format
  
- **services/xp20_server_service.py**: XP20 device emulation
  - Generates XP20-specific responses
  - Handles XP20 device configuration
  - Implements XP20 telegram format

### CLI Commands
```bash
xp server start    # Start the Conbus emulator server
xp server stop     # Stop the running emulator server
```

#### CLI Implementation
- **xp server start**:
  - Load config.yml
  - Initialize device services (XP20, XP24)
  - Start TCP server on port 10001
  - Display server status and listening port
  
- **xp server stop**:
  - Gracefully shutdown TCP server
  - Close all client connections
  - Clean up resources
  - Display shutdown confirmation

## Example Interaction
```
Client → Server: <S0000000000F01D00FA>
Server → Modules: <S0000000000F01D00FA>
Module → Server: <R2002022202F01DFM>
Server → Client: <R2002022202F01DFM>
Module → Server: <R2410010001F01DFK>
Server → Client: <R2410010001F01DFK>
```