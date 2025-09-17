# XP CLI Tool - LLM Agent Architecture Guide

## 🤖 AGENT OVERVIEW
**System Name:** XP CLI Tool  
**Purpose:** Python CLI for TCP communication with remote console bus devices  
**Target:** 192.168.0.1:1000  
**Agent Role:** Development assistant for modular, testable, maintainable code

## 🎯 CORE AGENT DIRECTIVES

### PRIMARY RULES (Always Follow)
1. **NEVER** bypass the layered architecture - respect connection → command → business → data flow
2. **ALWAYS** write tests BEFORE implementation (TDD approach)
3. **MUST** achieve 90%+ test coverage for any new code
4. **FORBIDDEN** to put business logic in CLI layer
5. **REQUIRED** to validate all inputs before processing
6. **MANDATORY** to handle all exceptions from exceptions.py

### CRITICAL CONSTRAINTS
- **XP24 Device:** Exactly 4 input channels (1-4), validate range strictly
- **XP20 Device:** Default action is "status" when no action specified
- **TCP Connection:** Always use tcp_client.py, never create direct sockets
- **Sensitive Data:** NEVER log serial numbers or device credentials
- **Output Format:** Always provide both human-readable AND JSON formats

## 🏗️ ARCHITECTURE LAYERS (Agent Implementation Guide)

### Layer 1: Connection Management
**Files:** `connection/tcp_client.py`, `connection/protocol.py`, `connection/exceptions.py`

**Agent Tasks:**
```python
# ALWAYS use this pattern for connections
def agent_connection_pattern():
    client = TCPClient("192.168.0.1", 10001)
    try:
        if client.connect():
            # Validate connection BEFORE sending commands
            response = client.send_command(command)
            return protocol.decode_response(response)
    except ConnectionError as e:
        # Handle from exceptions.py
        logger.error(f"Connection failed: {e}")
    finally:
        client.disconnect()
```

**FORBIDDEN Actions:**
- Creating raw sockets
- Bypassing connection validation
- Ignoring connection exceptions

### Layer 2: Command Interface 
**Files:** `cli/main.py`, `cli/commands.py`, `cli/validators.py`

**Agent Tasks:**
```python
# ALWAYS use this pattern for new commands
@cli.command()
@click.argument('param')
@validate_input  # REQUIRED decorator
def new_command(param):
    """ALWAYS include docstring"""
    # 1. Validate input (REQUIRED)
    # 2. Call business layer (NEVER implement logic here)
    # 3. Format output (human + JSON)
    
# REQUIRED output format
def format_response(data):
    return {
        "human": "Human readable text",
        "json": structured_data,
        "success": boolean
    }
```

**FORBIDDEN Actions:**
- Implementing business logic in CLI commands
- Skipping input validation
- Single-format output (must provide both human + JSON)

### Layer 3: Business Logic
**Files:** `services/module_service.py`, `services/xp24_service.py`, `services/xp20_service.py`

**Agent Tasks:**
```python
# ALWAYS implement core logic here
class ModuleService:
    def __init__(self, tcp_client):
        self.client = tcp_client  # Inject, don't create
    
    def process_command(self, params):
        # 1. Validate business rules
        # 2. Call connection layer
        # 3. Process response
        # 4. Return structured data
        
# Device-specific constraints (ENFORCE STRICTLY)
class XP24Service:
    MAX_INPUTS = 4  # NEVER exceed
    
    def validate_input_channel(self, channel):
        if not (1 <= channel <= self.MAX_INPUTS):
            raise ValidationError(f"Invalid input: {channel}")

class XP20Service:
    DEFAULT_ACTION = "status"  # Use when no action specified
```

**REQUIRED Patterns:**
- Dependency injection (don't create connections in services)
- Input validation at service level
- Structured error responses
- Device-specific constraint enforcement

### Layer 4: Data Models
**Files:** `models/module.py`, `models/response.py`

**Agent Tasks:**
```python
# ALWAYS use structured models
@dataclass
class Module:
    id: str
    name: str
    type: str
    status: str
    # NO sensitive data in logs
    
    def to_dict(self) -> dict:
        """REQUIRED for JSON serialization"""
        
class Response:
    def __init__(self, success: bool, data: Any, error: str = None):
        self.success = success
        self.data = data
        self.error = error
        # ALWAYS include timestamp
        self.timestamp = datetime.now()
```

## 🧪 TESTING REQUIREMENTS (Mandatory for Agents)

### Test-First Development Pattern
```python
# ALWAYS write test first
def test_new_feature():
    # Arrange
    mock_client = MockTCPClient(expected_responses)
    service = ModuleService(mock_client)
    
    # Act
    result = service.new_method(test_params)
    
    # Assert
    assert result.success == True
    assert "expected_value" in result.data

# THEN implement the actual method
def new_method(self, params):
    # Implementation here
```

### Coverage Requirements
- **Minimum:** 90% line coverage
- **Required:** Test all error paths
- **Mandatory:** Mock all external dependencies
- **Essential:** Integration tests for end-to-end flows

### Mock Strategy (Agent Must Follow)
```python
# ALWAYS mock external dependencies
class MockTCPClient:
    def __init__(self, responses: dict):
        self.responses = responses
        self.call_log = []  # Track calls for verification
    
    def send_command(self, command: str) -> bytes:
        self.call_log.append(command)
        return self.responses.get(command, b'error')
```

## 📁 PROJECT STRUCTURE (Agent Navigation Guide)



### Project Structure
```
xp/
├── src/
│   └── xp/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py              # Entry point and CLI setup
│       │   ├── commands.py          # Command implementations
│       │   └── validators.py        # Input validation
│       ├── connection/
│       │   ├── __init__.py
│       │   ├── tcp_client.py        # TCP socket management
│       │   ├── protocol.py          # Console bus protocol
│       │   └── exceptions.py        # Connection exceptions
│       ├── services/
│       │   ├── __init__.py
│       │   ├── module_service.py    # Module operations
│       │   ├── xp24_service.py      # XP24 device operations
│       │   └── xp20_service.py      # XP20 device operations
│       └── models/
│           ├── __init__.py
│           ├── module.py            # Module data structures
│           └── response.py          # Response models
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_cli/
│   │   ├── test_connection/
│   │   ├── test_services/
│   │   └── test_models/
│   ├── integration/
│   │   ├── test_tcp_integration.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── mock_responses.py
│       └── test_data.py
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
        
```

## Command Specifications
### Core Commands
#### list modules

Lists all available modules on the remote console bus
Returns module ID, name, type, and status
Usage: xp list modules

#### info <module>

Retrieves detailed information about a specific module
Returns configuration, status, and capabilities
Usage: xp info MODULE_NAME

#### update serial <module>

Updates the serial number for a specified module
Validates serial number format before transmission
Usage: xp update serial MODULE_NAME NEW_SERIAL

### XP24 Device Commands
#### xp24 action input <1-4>

Triggers action on XP24 device input channels (1-4)
Validates input channel range
Usage: xp xp24 action input 2

#### xp24 detail <module>

Retrieves XP24-specific module details
Returns input/output states, configurations, and diagnostics
Usage: xp xp24 detail MODULE_NAME

### XP20 Device Commands
#### xp20 action

Executes XP20 device-specific actions
Usage: xp xp20 action

## Technical Implementation
### TCP Connection Management

```python
class TCPClient:
    """Manages TCP socket connection to remote console bus"""
    
    def __init__(self, host: str = "192.168.0.1", port: int = 10001):
        self.host = host
        self.port = port
        self.socket = None
        self.timeout = 30
    
    def connect(self) -> bool:
        """Establishes connection with retry logic"""
    
    def send_command(self, command: str) -> bytes:
        """Sends command and returns raw response"""
    
    def disconnect(self) -> None:
        """Safely closes connection"""
```

### Protocol Handler
```python

class ConsoleProtocol:
    """Handles remote console bus protocol"""
    
    def encode_command(self, command: str, params: dict) -> bytes:
        """Encodes command for transmission"""
    
    def decode_response(self, raw_data: bytes) -> dict:
        """Parses response into structured data"""
    
    def validate_response(self, response: dict) -> bool:
        """Validates response integrity"""

```
### CLI Interface

```python
@click.group()
@click.option('--host', default='192.168.0.1')
@click.option('--port', default=10001)
@click.pass_context
def cli(ctx, host, port):
    """xp CLI tool for remote console bus operations"""
    
@cli.command()
def list_modules():
    """List all available modules"""
    
@cli.command()
@click.argument('module')
def info(module):
    """Get detailed module information"""

```

## Test-Driven Development Strategy

### Unit Tests (>90% coverage target)

- Individual component testing
- Mock external dependencies
- Edge case validation
- Error handling verification

### Integration Tests

- TCP connection functionality
- Protocol communication
- End-to-end command execution
- Error propagation testing

### Acceptance Tests

- User story validation
- CLI interface testing
- Real device interaction (when available)
- Performance benchmarking

### Test Implementation Approach

- Red Phase: Write failing tests for each feature
- Green Phase: Implement minimal code to pass tests
- Refactor Phase: Optimize code while maintaining test coverage

### Mock Strategy
```python
class MockTCPConnection:
    """Mock TCP connection for testing"""
    
    def __init__(self, responses: dict):
        self.responses = responses
    
    def send_command(self, command: str) -> bytes:
        return self.responses.get(command, b'')
```

## Error Handling
### Exception Hierarchy

```python
class xpError(Exception):
    """Base exception for xp"""

class ConnectionError(xpError):
    """TCP connection related errors"""

class ProtocolError(xpError):
    """Console bus protocol errors"""

class ValidationError(xpError):
    """Input validation errors"""

class ModuleNotFoundError(xpError):
    """Module not found on remote bus"""
```

## Logging Strategy

- Structured logging with JSON format
- Configurable log levels (DEBUG, INFO, WARN, ERROR)
- Separate logs for connection events and command execution
- Performance metrics logging

## Configuration Management
### Configuration File Support
```yaml
# xp.yml
connection:
  host: "192.168.0.1"
  port: 10001
  timeout: 30
  retry_attempts: 3

logging:
  level: "INFO"
  format: "json"
  file: "xp.log"

devices:
  xp24:
    input_channels: 4
    validation_strict: true
  xp20:
    default_action: "status"
```

## Security Considerations
### Network Security

- Connection timeout enforcement
- Input sanitization for all commands
- Protocol message validation
- Rate limiting for command execution

### Data Protection

- No sensitive data logging
- Secure handling of serial numbers
- Connection state cleanup
- Memory-safe string operations

## Performance Requirements
### Response Time Targets

- Command execution: < 2 seconds
- Module listing: < 5 seconds
- Connection establishment: < 3 seconds
- Error recovery: < 1 second

### Resource Constraints

- Memory usage: < 50MB baseline
- CPU usage: < 10% during normal operations
- Network bandwidth: < 1KB/s average
- Concurrent connections: 1 (single-threaded design)

## Deployment and Distribution
### Package Distribution
```python
# setup.py configuration
setup(
    name="xp",
    version="1.0.0",
    entry_points={
        'console_scripts': [
            'xp=xp.cli.main:cli',
        ],
    },
    install_requires=[
        "click>=8.0",
        "pyyaml>=6.0",
        "structlog>=22.0",
    ]
)
```
### Installation Methods

- PyPI package distribution
- Standalone executable generation
- Development installation with pip -e

