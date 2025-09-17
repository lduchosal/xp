# Conbus Reverse Proxy Specification

## Overview
A TCP reverse proxy that intercepts Conbus client connections and forwards telegrams to the configured Conbus server. Provides transparent telegram routing with real-time monitoring of all communications.

## Network Architecture
```
Client → Reverse Proxy (port 10001) → Conbus Server (cli.yml configured)
```

## Core Functionality

### TCP Server
- **Protocol**: TCP
- **Listen Port**: 10001
- **Binding**: All interfaces (0.0.0.0:10001)
- **Connection**: Multiple concurrent clieplementnt connections
- **Timeout**: 30 seconds for idle connections

### Target Server Configuration
The reverse proxy reads target server configuration from `cli.yml`:
```yaml
conbus:
  ip: 10.0.3.162
  port: 10001
  timeout: 10
```

### Bidirectional Relay
For each client connection:
1. **Accept** incoming client connection on port 10001
2. **Connect** to target server using cli.yml configuration
3. **Relay** all data bidirectionally between client and server
4. **Monitor** and print all telegrams in both directions
5. **Close** both connections when either side disconnects

## Telegram Monitoring

### Output Format
All telegrams are printed with timestamps and direction indicators:
```
HH:MM:SS,mmm [CLIENT→PROXY] <telegram>
HH:MM:SS,mmm [PROXY→SERVER] <telegram>
HH:MM:SS,mmm [SERVER→PROXY] <telegram>
HH:MM:SS,mmm [PROXY→CLIENT] <telegram>
```

### Example Session
```
14:32:15,123 [CLIENT→PROXY] <S0000000000F01D00FA>
14:32:15,124 [PROXY→SERVER] <S0000000000F01D00FA>
14:32:15,157 [SERVER→PROXY] <R0020030837F01DFM>
14:32:15,158 [PROXY→CLIENT] <R0020030837F01DFM>
14:32:15,201 [SERVER→PROXY] <R0020044966F01DFK>
14:32:15,202 [PROXY→CLIENT] <R0020044966F01DFK>
14:32:15,201 [SERVER→PROXY] <E071299939AK>
```

## Implementation Requirements

### Core Components
- **services/conbus_reverse_proxy_service.py**: Main proxy implementation
  - TCP server socket management
  - Client connection handling
  - Server connection establishment
  - Bidirectional data relay
  - Telegram logging and monitoring

### Connection Management
- **Client Connections**: Accept single connections
- **Server Connections**: Single server connection for all clients connection
- **Error Handling**: Graceful disconnection on either side
- **Resource Cleanup**: Proper socket closure and thread termination

### Configuration Loading
- Read target server details from `cli.yml`
- Default fallback values if configuration is missing

### Logging and Monitoring
- Real-time telegram display to console
- File logging for audit trail
- Connection establishment/termination events
- Error conditions and network failures

## CLI Interface

### Start Reverse Proxy
```bash
xp rp start    # Start reverse proxy on port 10001
```

### Stop Reverse Proxy
```bash
xp rp stop     # Stop running reverse proxy
```

### Status Check
```bash
xp rp status   # Show proxy status and active connections
```

## Error Handling

### Connection Failures
- **Client Disconnect**: Close corresponding server connection
- **Server Disconnect**: Close corresponding client connection  
- **Server Unreachable**: Return connection error to client
- **Configuration Error**: Log error and use fallback settings

### Network Issues
- **Timeout Handling**: Apply configured timeout values
- **Retry Logic**: Attempt reconnection on temporary failures
- **Graceful Degradation**: Continue serving other connections

## Technical Considerations

### Threading Model
- Main thread: Accept client connections
- Worker threads: Handle individual client-server pairs
- Thread pool: Manage concurrent connections efficiently

### Data Handling
- **Encoding**: latin-1 (consistent with existing Conbus implementation)
- **Buffer Size**: 1024 bytes per read operation
- **Telegram Detection**: Monitor for complete telegram boundaries
- **Flow Control**: Handle different read/write speeds between sides

### Performance
- **Minimal Latency**: Direct data relay without processing
- **Low Overhead**: Simple pass-through architecture
- **Scalability**: Support reasonable number of concurrent connections

### Security
- **Access Control**: Listen only on required interfaces
- **Data Integrity**: Preserve telegram content without modification
- **Resource Limits**: Prevent resource exhaustion attacks

## Example Implementation Flow

1. **Startup**:
   - Load configuration from cli.yml
   - Create TCP server socket on port 10001
   - Start accepting client connections

2. **Client Connection**:
   - Accept client socket
   - Establish connection to target server
   - Create bidirectional relay threads
   - Begin telegram monitoring

3. **Data Relay**:
   - Read data from client → forward to server
   - Read data from server → forward to client
   - Print all telegrams with timestamps
   - Handle connection errors gracefully

4. **Cleanup**:
   - Close both client and server sockets
   - Terminate relay threads
   - Log connection termination

## Integration Testing

### Test Scenarios
1. **Discovery Request**: Verify discovery telegrams are properly relayed
2. **Version Requests**: Test version query forwarding and responses  
3. **Sensor Data**: Validate sensor telegram relay functionality
4. **XP Inputs**: Ensure XP24 action commands work through proxy
5. **Multiple Clients**: Test concurrent client connections
6. **Error Conditions**: Verify graceful handling of failures

### Validation Criteria
- All telegrams forwarded without modification
- Timestamps accurate for monitoring
- No data loss during relay
- Proper connection cleanup
- Configuration changes respected
