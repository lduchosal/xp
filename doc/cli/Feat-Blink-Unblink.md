# Function Blink and Unblink

The function of a "Blink" of a conson modules control LED on the front panel:
- Blinks an LED on and off at regular intervals
- Often used as a status indicator (system alive)
- Identify module, see physical LED activity

## Blink function: 05 
Telegram:<S0012345008F05D00FN>
Type: System
Serial: 0012345008
Function: 05
DataPoint: 00

Telegram:<R0012345008F18DFA>
Type: Response
Serial: 0012345008
Function: 18 (ACK)
DataPoint:  


## Unblink function: 06

Telegram:<S0012345011F06D00FJ>
Type: System
Serial: 0012345011
Function: 06
DataPoint: 00

Telegram:<R0012345011F18DFA>
Type: Response
Serial: 0012345011
Function: 18 (ACK)
DataPoint:  

## Cli commands

xp blink <serial>
xp unblink <serial>

xp/cli/commands/blink_commands.py

## models

xp/models/blink_telegram.py (inherits telegram)

## services

xp/services/blink_service.py

---

## Implementation Notes

### 🔗 Similarity to LINK_NUMBER Functionality

The blink/unblink feature implementation follows a very similar pattern to the existing `link_number` functionality:

#### **Blink Implementation Pattern (New)**
- **Service**: `src/xp/services/blink_service.py` (to be created)
- **CLI Commands**: `src/xp/cli/commands/blink_commands.py` (to be created)  
- **System Functions**: Uses `F05` (BLINK) and `F06` (UNBLINK)
- **Data Points**: Uses DataPointType.STATUS (`00`)
- **Telegram Format**: 
  - Blink: `<S{serial}F05D00{checksum}>`
  - Unblink: `<S{serial}F06D00{checksum}>`

#### **Key Similarities**
1. **Service Layer Structure**: Both services handle telegram generation, validation, and parsing
2. **CLI Command Pattern**: Both use Click decorators with `@json_output_option` and error handling
3. **Validation Logic**: Serial number validation (10 digits, numeric only)
4. **Response Handling**: ACK/NAK response parsing for confirmation
5. **Error Management**: Custom exception classes (`LinkNumberError` vs `BlinkError`)
6. **Testing Strategy**: Unit tests for service methods, integration tests for end-to-end

#### **Key Differences**
1. **Function Codes**: Link number uses F03/F04, Blink uses F05/F06
2. **Data Values**: Link number has variable data (0-99), Blink uses fixed D00
3. **No Read Operation**: Blink doesn't need a "read current blink status" equivalent
4. **State Management**: Blink is stateless (on/off), Link number persists configuration

### 💡 Implementation Strategy

**Phase 1: Copy & Adapt LINK_NUMBER Structure**
- Copy `link_number_service.py` → `blink_service.py`
- Copy `linknumber_commands.py` → `blink_commands.py`
- Adapt telegram generation methods for F05/F06 functions
- Update validation logic (remove value range checks)

**Phase 2: Add Blink-Specific Enums**
- Add `SystemFunction.BLINK = "05"` and `SystemFunction.UNBLINK = "06"` to `system_telegram.py`
- Use existing `DataPointType.STATUS = "00"`

**Phase 3: Testing Strategy**
- Copy test structure from `test_link_number_service.py`
- Update test telegrams and expected values
- Focus on ACK response validation (no data parsing needed)

---

## Implementation Checklist

### 📋 Layer 1: Connection Management
- [ ] Update `connection/protocol.py` to handle blink/unblink telegram formats
  - [ ] Add `encode_blink_command()` method for function 05
  - [ ] Add `encode_unblink_command()` method for function 06
  - [ ] Add `decode_blink_response()` method for ACK parsing
- [ ] Update `connection/exceptions.py` with blink-specific exceptions
  - [ ] Add `BlinkOperationError` exception class
  - [ ] Add `BlinkTimeoutError` exception class

### 📋 Layer 2: CLI Command Interface
- [ ] Add blink commands to `cli/commands.py`
  - [ ] Implement `blink` command: `xp blink <module_serial>`
  - [ ] Implement `unblink` command: `xp unblink <module_serial>`
  - [ ] Add `--timeout` option for blink duration
- [ ] Update `cli/validators.py` with blink input validation
  - [ ] Add `validate_module_serial()` function
  - [ ] Add `validate_blink_timeout()` function
- [ ] Update `cli/main.py` to register new commands
  - [ ] Add blink command group
  - [ ] Configure command help text and examples

### 📋 Layer 3: Business Logic Services  
- [ ] Create `services/blink_service.py`
  - [ ] Implement `BlinkService` class
  - [ ] Add `start_blink(module_serial: str)` method
  - [ ] Add `unblink(module_serial: str)` method
  - [ ] Add `get_blink_status(module_serial: str)` method
  - [ ] Implement proper error handling and logging
- [ ] Update existing module services to support blink operations
  - [ ] Update `services/module_service.py` to integrate blink functionality
  - [ ] Add blink status to module information responses

### 📋 Layer 4: Data Models
- [ ] Update `models/response.py` 
  - [ ] Add `BlinkResponse` dataclass
  - [ ] Add `BlinkStatus` enum (OFF, BLINKING, ERROR)
- [ ] Update `models/module.py`
  - [ ] Add `blink_status` field to Module dataclass
  - [ ] Add `last_blink_command` timestamp field
- [ ] Create `models/blink.py` for blink-specific models
  - [ ] Add `BlinkCommand` dataclass
  - [ ] Add `BlinkTelegram` dataclass with parsing methods

### 📋 Testing Requirements (90%+ Coverage)
- [ ] Unit Tests - `tests/unit/`
  - [ ] `test_blink_service.py` - Test all BlinkService methods
  - [ ] `test_blink_models.py` - Test blink data models
  - [ ] `test_blink_commands.py` - Test CLI command parsing
  - [ ] `test_blink_protocol.py` - Test telegram encoding/decoding
- [ ] Integration Tests - `tests/integration/`
  - [ ] `test_blink_integration.py` - End-to-end blink workflow
  - [ ] `test_blink_tcp_integration.py` - TCP communication with mock responses
- [ ] Mock Strategy
  - [ ] Create `MockBlinkResponses` in `tests/fixtures/mock_responses.py`
  - [ ] Add blink telegram samples to `tests/fixtures/test_data.py`
  - [ ] Update `MockTCPClient` to handle blink commands

### 📋 Error Handling & Edge Cases
- [ ] Handle invalid module serials gracefully
- [ ] Implement timeout handling for blink operations
- [ ] Handle concurrent blink requests to same module
- [ ] Add proper error messages for user feedback
- [ ] Implement retry logic for failed blink commands

### 📋 Documentation & Usage
- [ ] Update command help text with examples
- [ ] Add blink commands to CLI usage documentation
- [ ] Include telegram format specifications
- [ ] Add troubleshooting guide for blink failures

### 📋 Performance & Security
- [ ] Validate serial number format before transmission
- [ ] Implement rate limiting for blink commands
- [ ] Add logging for blink operations (no sensitive data)
- [ ] Ensure proper connection cleanup after blink operations

### 📋 Acceptance Criteria
- [ ] CLI commands `xp blink <serial>` and `xp unblink <serial>` work correctly
- [ ] Commands return both human-readable and JSON formatted responses
- [ ] All tests pass with 90%+ coverage
- [ ] Error handling provides meaningful feedback to users
- [ ] Integration with existing module management commands
- [ ] No performance regression in connection management
