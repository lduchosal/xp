# Conbus Client Send Specification

## Overview
The Conbus Client is a network client that connects to a Conbus server to send various types of sensor and system data via UDP telegrams.

## Connection Details
- **Protocol**: TCP
- **Target IP**: Configurable IP address
- **Port**: 10001
- **Connection Type**: Client-to-server telegram communication

## Supported Telegrams Types

The client supports sending the following telegram types:

### 1. Discovery
- **Purpose**: Announce client presence to the server
- **Type**: `discovery`
- **Description**: Used for service discovery and client registration

### 2. Version
- **Purpose**: Report client software version
- **Type**: `version`
- **Description**: Sends current client version information to the server

### 3. VOLTAGE
- **Purpose**: Report voltage measurements
- **Type**: `voltage`
- **Description**: Transmits voltage sensor readings

### 4. Temperature
- **Purpose**: Report temperature measurements
- **Type**: `temperature`
- **Description**: Transmits temperature sensor readings

### 5. Current
- **Purpose**: Report current measurements
- **Type**: `current`
- **Description**: Transmits electrical current sensor readings

### 6. Humidity
- **Purpose**: Report humidity measurements
- **Type**: `humidity`
- **Description**: Transmits humidity sensor readings

## Implementation Requirements

### Core Functionality
- Establish TCP connection to specified IP address on port 10001
- Support for all six telegram types listed above
- Reliable telegram transmission
- Error handling for network connectivity issues

### Configuration
- Configurable target IP address
- Configurable transmission intervals for each telegram type
- Optional retry mechanism for failed transmissions
- Configuration loaded from `cli.yml` file

#### Configuration File Format (cli.yml)
```yaml
conbus:
  ip: 192.168.1.100
  port: 10001
  timeout: 10
```

**Configuration Parameters:**
- `ip`: Target server IP address (default: 192.168.1.100)
- `port`: Target server port (default: 10001)  
- `timeout`: Connection timeout in seconds (default: 10)

### Data Format
- Telegrams should follow a consistent format structure
- Include timestamp information
- Include client identification
- Support for sensor data values with appropriate units

## CLI Examples

### Basic Usage
```bash
# Connect to server and send discovery telegram
xp conbus send discovery

# Request version information
xp conbus send 0020030837 version

# Request sensor data
xp conbus send 0020030837 voltage
xp conbus send 0020030837 temperature
xp conbus send 0020030837 current

# Request custom function with data
xp conbus send 0020030837 custom 02 E2

```

### Connection Management
```bash
# display configuration
xp conbus config
```

## Output Samples

### Configuration Display
```bash
$ xp conbus config
  ip: 192.168.1.100
  port: 10001
  timeout: 10 miliseconds
```

### Discovery Command
```bash
$ xp conbus send discovery
22:48:38,646 [TX] <S0000000000F01D00FA>
22:48:38,672 [RX] <R0020030837F01DFM>
22:48:38,726 [RX] <R0020044966F01DFK>
22:48:38,772 [RX] <R0020042796F01DFN>
22:48:38,772 [RX] <R0020044991F01DFC>
22:48:38,820 [RX] <R0020044964F01DFI>
22:48:38,820 [RX] <R0020044986F01DFE>
22:48:38,820 [RX] <R0020037487F01DFM>
22:48:38,866 [RX] <R0020044989F01DFL>
22:48:38,866 [RX] <R0020044974F01DFJ>
22:48:38,913 [RX] <R0020041824F01DFI>
```

### Version Request
```bash
$ xp conbus send 0020030837 version
22:48:42,952 [TX] <S0020030837F02D02FM>
22:48:42,981 [RX] <R0020030837F02D02XP230_V1.00.04FI>
```

### Sensor Data Request
```bash
$ xp conbus send 0020030837 voltage
22:48:42,952 [TX] <S0020030837F02D20FM>
22:48:42,981 [RX] <R0020030837F02D20+12.5V§OK>

$ xp conbus send 0020030837 temperature
22:48:42,952 [TX] <S0020012521F02D18FM>
22:48:42,981 [RX] <R0020012521F02D18+23.4C§OK>
```

### Custom Function
```bash
$ xp conbus send 0020030837 custom fuction 02 datapoint E2
22:48:42,952 [TX] <S0020030837F02DE2FM>
22:48:42,952 [RX] <R0020030837F02DE2COUCOUFM>
```

### Error Handling
```bash
$ xp conbus send discovery
Connecting to 192.168.1.100:10001...
Error: Connection timeout after 10 seconds
Failed to connect to server

$ xp conbus send 9999999999 version
22:48:42,952 [TX] <S0020012521F02D18FM>
```

## Technical Considerations
- Handle network disconnections gracefully
- Implement appropriate timeouts for TCP operations
- Consider data serialization format (JSON, binary, etc.)
- Log transmission attempts and failures for debugging