# Feature: Conbus Scan

## Overview
Send telegram to scan all functions and all datapoints for a module.

## Telegram Format
System telegrams are identified by the "S", and followed by the receiver serial number. The two digits after "F" designates the system function (here "Read Data point"), and the two digits after "D" is the data point ID (here temperature).

## Requirements
- Scan all available functions for a specified module
- Scan all available datapoints for each function
- Return comprehensive data about module capabilities
- Handle module response errors gracefully

## Implementation Notes
- The two digits after "F" designates the system function
- The two digits after "D" is the data point ID
- Integrates into existing `xp conbus` command group
- Reuses existing ConbusDatapointService for communication
- Follows existing CLI patterns and output formatting

### Command Integration
The scan command will be integrated as:
```bash
xp conbus scan <serial_number>
```

### Expected Output
```bash
$ xp conbus scan 0020030837
22:48:38,646 [TX] <S0020030837F00D00XX>
22:48:38,672 [TX] <S0020030837F00D01XX>
22:48:38,672 [TX] <S0020030837F00D02XX>
22:48:38,672 [TX] <S0020030837F00D03XX>
22:48:38,672 [TX] <S0020030837F00D04XX>
...
22:48:38,672 [TX] <S0020030837F01D00XX>
```

### Technical Implementation
- Extends existing ConbusDatapointService with scan functionality
- Systematically iterates through function codes (00-FF)
- For each function, scans datapoint codes (00-FF)  
- Uses existing telegram generation and communication infrastructure
- Supports --json-output flag for structured results
- **Background Processing**: Scan operations run in background with real-time output
- **Live Output Display**: Results are displayed as they arrive from the server
- Small delays between requests prevent server overload