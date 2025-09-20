# Feature XP24-Action: Remote Action Control for XP24 Modules

## Overview

XP24 modules are remote switch devices that can be commanded via the conbus. Each XP24 module has 4 inputs that control 4 relays, allowing remote activation and deactivation of electrical circuits.

## Module Information

- **Module Type**: XP24 (Module Type Code: 07)
- **Example Serial**: 0020044964
- **Inputs**: 4 inputs (0-3) that control 4 corresponding relays
- **Communication**: Console bus telegrams

## Telegram Formats

### Action Command (System Telegram)
**Format**: `<S{serial_number}F27D{input}{action}{checksum}>`

**Example**: `<S0020044964F27D00AAFN>`
- **Type**: System (S)
- **Module**: 0020044964 
- **Function**: 27 (action on input)
- **DataPoint**: 00AA (input 0, action AA)

### Acknowledgment (Reply Telegram)
**Format**: `<R{serial_number}F18D{checksum}>`

**Example**: `<R0020044964F18DFA>`
- **Type**: Reply (R)
- **Module**: 0020044964 
- **Function**: 18 (Acknowledge)
- **DataPoint**: NULL

### Status Query (System Telegram)
**Format**: `<S{serial_number}F02D12{checksum}>`

**Example**: `<S0020044964F02D12FJ>`
- **Type**: System (S)
- **Module**: 0020044964 
- **Function**: 02 (Read Data point)
- **DataPoint**: 12 (inputs status)

### Status Response (Reply Telegram)
**Format**: `<R{serial_number}F02D12xxxx{status}{checksum}>`

**Example**: `<R0020044964F02D12xxxx1110FJ>`
- **Type**: Reply (R)
- **Module**: 0020044964 
- **Function**: 02 (Read Data point)
- **DataPoint**: 12xxxx1110 (inputs status: ON ON ON OFF)

### Event Notification (Event Telegram)
**Format**: `<E07L{link_number}I8{input}{action}{checksum}>`

**Example**: `<E07L06I80BAL>`
- **Type**: Event (E)
- **Module Type**: 07 (XP24)
- **LINK_NUMBER**: 06
- **Input Number**: 80 (input 0)
- **Button**: B (Break/release), M (Make/press)

## Sample CLI Commands

```bash
# Send action command to XP24 module
xp conbus xp24 0020044964 0
xp conbus xp24 0020044964 1
xp conbus xp24 0020044964 2
xp conbus xp24 0020044964 3

# Query status of XP24 module
xp conbus xp24 0020044964 status

```

## Communication Flow Example

```conbus
[TX] <S0020044964F27D00AAFN>      # Send action to input 0 (press)
[RX] <R0020044964F18DFA>          # Receive acknowledgment
[TX] <S0020044964F02D12FJ>        # Query status
[RX] <E07L06I80BAL>               # Event: input 0 released
[RX] <R0020044964F02D12xxxx1110FJ> # Status: inputs 1110 (ON ON ON OFF)
```

## Implementation

### Models (src/xp/models/)

#### XP24ActionTelegram
```python
@dataclass
class XP24ActionTelegram(Telegram):
    """XP24 action telegram model"""
    serial_number: str
    output_number: int  # 0-3
    action_type: ActionType  # PRESS/RELEASE
    checksum: str
```

#### ActionType Enum
```python
class ActionType(Enum):
    PRESS = "AA"    # Make action
    RELEASE = "AB"  # Break action
```

### Services (src/xp/services/)

#### XP24ActionService
```python
class XP24ActionService:
    """Service for XP24 action operations"""
    
    def send_action(self, serial: str, input_num: int, action: ActionType) -> bool
    def query_status(self, serial: str) -> Dict[int, bool]
    def parse_action_telegram(self, raw: str) -> XP24ActionTelegram
    def validate_action_telegram(self, telegram: XP24ActionTelegram) -> bool
```

### CLI Commands (src/xp/cli/commands/)

#### Enhancement to conbus_commands.py
```python
@conbus.command("xp24")
@click.argument('serial_number')
@click.argument('output_number_or_status', type=click.IntRange(0, 3))
@connection_command()
@handle_service_errors(ConbusClientSendError)
def xp_action(serial_number: str, output_number: int, action: str, json_output: bool):
    """
    Send action command to XP24 module or query status.
    
    Examples:

    \b
    xp conbus xp24 0020044964 0        # Toggle input 0
    xp conbus xp24 0020044964 1        # Toggle input 1  
    xp conbus xp24 0020044964 2        # Toggle input 2
    xp conbus xp24 0020044964 3        # Toggle input 3
    
    xp conbus xp24 0020044964 status   # Toggle ON ON ON OFF
    """
```

## Tests

### Unit Tests
- `tests/unit/test_models/test_input_telegram.py`
- `tests/unit/test_services/test_xp24_action_service.py`
- `tests/unit/test_cli/test_action_commands.py`

### Integration Tests
- `tests/integration/test_xp24_action_integration.py`

### Test Coverage Requirements
- Models: 95%+ coverage
- Services: 90%+ coverage  
- CLI: 85%+ coverage

## Implementation Checklist

### Phase 1: Core Models
- [ ] Create `ActionType` enum with PRESS/RELEASE values
- [ ] Implement `XP24ActionTelegram` dataclass
- [ ] Add telegram validation methods
- [ ] Add human-readable string representations
- [ ] Unit tests for models (95%+ coverage)

### Phase 2: Services
- [ ] Implement `XP24ActionService` class
- [ ] Add `send_action()` method for command transmission
- [ ] Add `query_status()` method for status queries
- [ ] Add `parse_action_telegram()` method
- [ ] Add telegram validation and checksum verification
- [ ] Unit tests for services (90%+ coverage)

### Phase 3: CLI Integration
- [ ] Create `action_commands.py` with click commands
- [ ] Implement `send` command for action transmission
- [ ] Implement `status` command for status queries
- [ ] Implement `parse` command for telegram parsing
- [ ] Implement `monitor` command for event listening
- [ ] Add proper error handling and user feedback
- [ ] CLI unit tests (85%+ coverage)

### Phase 4: System Integration
- [ ] Update main CLI to register action commands
- [ ] Add action service to service registry
- [ ] Integration tests for end-to-end workflows
- [ ] Test with real XP24 hardware (if available)
- [ ] Documentation updates

### Phase 5: Advanced Features
- [ ] Batch action commands for multiple inputs
- [ ] Action scheduling and timing
- [ ] Event filtering and monitoring
- [ ] Configuration management for XP24 modules
- [ ] Performance optimization and caching

## Technical Notes

### Input Encoding
- Inputs are encoded as 0-3 (decimal)
- In telegrams, input 0 = "00", input 1 = "01", etc.
- Event telegrams use 80-83 format (80 = input 0)

### Action Encoding
- Press action: "AA" (Make)
- Release action: "AB" (Break)

### Status Encoding
- Status returned as 4-bit binary string
- "1110" = inputs 0,1,2 ON, input 3 OFF
- "0000" = all inputs OFF
- "1111" = all inputs ON

### Error Handling
- Invalid serial numbers (must be 10 digits)
- Invalid input numbers (must be 0-3)
- Communication timeouts
- Checksum validation failures
- Module not responding

## Dependencies
- Existing telegram parsing infrastructure
- Checksum calculation utilities
- Console bus communication services
- Click CLI framework