# XP Protocol Communication Tool

A comprehensive Python CLI and API tool for CONSON XP Protocol operations, including console bus (Conbus) communication, telegram parsing, HomeKit integration, and module management.

## Features

### Core Communication
- **Conbus Operations**: Send and receive telegrams via TCP connections to XP130 and XP230 servers
- **Telegram Parsing**: Parse event, system, and reply telegrams from remote console bus devices
- **Real-time Communication**: Bidirectional communication with XP protocol devices
- **Server Discovery**: Automatic discovery of XP servers on the network

### Protocol Support
- **Multiple XP Modules Types**: XP20, XP24, XP33, XP130, XP230, CP20 server support
- **Telegram Types**: Event, system, reply, output, and blink telegrams
- **Checksum Validation**: Multiple checksum algorithms for data integrity
- **Link Number Management**: Handle telegram versioning and link numbers

### Device Management
- **Module Type Database**: Comprehensive module type information and search
- **Datapoint Operations**: Read/write datapoints on connected devices
- **Output Control**: Control outputs on XP devices
- **Blink Operations**: Visual feedback and device identification

### Integration & APIs
- **REST API**: FastAPI-based REST endpoints for all operations
- **HomeKit Integration**: Apple HomeKit bridge for smart home integration
- **Configuration Management**: YAML-based configuration with validation
- **Reverse Proxy**: Proxy server for device communication

### Development & Testing
- **JSON Output**: All commands support both human-readable and JSON output formats
- **Comprehensive Testing**: 90%+ test coverage with unit and integration tests
- **Modern Python**: Type hints, async/await, and modern Python practices

## Installation

### Using PDM (Recommended)
```bash
git clone <repository-url>
cd xp
pdm install
```

### Using pip
```bash
git clone <repository-url>
cd xp
pip install -e .
```

### Development Installation
```bash
# Using PDM
pdm install -G dev

# Using pip
pip install -e ".[dev]"
```

## Usage

### Telegram Operations

Parse different types of telegrams:

```bash
# Parse event telegram
xp telegram parse "<E14L00I02MAK>"

# Parse system telegram
xp telegram parse "<S0020012521F02D18FN>"

# Parse reply telegram
xp telegram parse "<R0020012521F02D18+26,0§CIL>"

# Auto-detect telegram type
xp telegram parse "<E14L00I02MAK>"

# Parse multiple telegrams from data stream
xp telegram parse-multiple "Data <E14L00I02MAK> more <E14L01I03BB1>"

# Validate telegram format and checksum
xp telegram validate "<E14L00I02MAK>"
```

### Module Type Operations

Manage and query module types:

```bash
# Get module information by ID or name
xp module info 14
xp module info XP2606

# List all modules
xp module list

# List modules by category
xp module list --category "Interface Panels"

# Group modules by category
xp module list --group-by-category

# Search modules
xp module search "push button"
xp module search --field name "XP"

# List available categories
xp module categories
```

### Checksum Operations

Calculate and validate checksums:

```bash
# Calculate simple checksum
xp checksum calculate "E14L00I02M"

# Calculate CRC32 checksum
xp checksum calculate "E14L00I02M" --algorithm crc32

# Validate checksum
xp checksum validate "E14L00I02M" "AK"

# Validate CRC32 checksum
xp checksum validate "E14L00I02M" "ABCDABCD" --algorithm crc32
```

### Conbus Operations

Connect to XP servers and perform real-time operations:

```bash
# Send custom telegrams to server
xp conbus custom <host> <port> <telegram>

# Discover XP servers on network
xp conbus discover

# Send blink commands
xp conbus blink <host> <port> <module_id> <datapoint>
xp conbus blink all <host> <port>  # Blink all modules

# Control outputs
xp conbus output <host> <port> <module_id> <datapoint> <value>

# Read/write datapoints
xp conbus datapoint read <host> <port> <module_id> <datapoint>
xp conbus datapoint write <host> <port> <module_id> <datapoint> <value>

# Receive real-time telegrams
xp conbus receive <host> <port>

# Send raw telegrams
xp conbus raw <host> <port> <raw_data>

# Scan for connected modules
xp conbus scan <host> <port>
```

### API Server

Start the FastAPI REST server:

```bash
# Start API server (default: localhost:8000)
xp api start

# Start with custom host and port
xp api start --host 0.0.0.0 --port 8080

# Start with auto-reload for development
xp api start --reload
```

API endpoints are available at:
- `/docs` - Interactive API documentation
- `/health` - Health check endpoint
- `/conbus/*` - Conbus operation endpoints

### HomeKit Integration

Manage HomeKit bridge for smart home integration:

```bash
# Validate HomeKit and Conson configuration
xp homekit config validate

# Show configuration summary
xp homekit config show

# Start HomeKit bridge
xp homekit start

# Start with custom configuration files
xp homekit start --conson-config custom-conson.yml --homekit-config custom-homekit.yml
```

### Server Management

Manage XP protocol servers:

```bash
# Start different server types
xp server start --type xp130 --port 10001
xp server start --type xp230 --port 10002
xp server start --type cp20 --port 10003

# Start reverse proxy
xp reverse-proxy start --target-host 192.168.1.100 --target-port 10001
```

### File Operations

Process telegram files and logs:

```bash
# Parse telegrams from file
xp file parse telegrams.txt

# Process log files
xp file process-log logfile.txt

# Extract telegrams from mixed content
xp file extract-telegrams mixed-data.txt
```

### JSON Output

Add `--json-output` or `-j` to any command for JSON formatted output:

```bash
xp telegram parse "<E14L00I02MAK>" --json-output
xp module info 14 -j
xp checksum calculate "E14L00I02M" -j
xp conbus discover -j
```

## Architecture

The project follows a layered architecture with clear separation of concerns:

### Core Layers
- **CLI Layer** (`cli/`): Command-line interface with modular command structure
- **API Layer** (`api/`): FastAPI REST endpoints with CORS support
- **Services Layer** (`services/`): Business logic and protocol implementations
- **Models Layer** (`models/`): Pydantic data models and response structures
- **Utils Layer** (`utils/`): Utility functions and helpers
- **Connection Layer** (`connection/`): Network communication and protocol handling

### Key Components
- **Telegram Processing**: Parse and validate XP protocol telegrams
- **Conbus Communication**: Real-time TCP/UDP communication with XP servers
- **HomeKit Bridge**: Apple HomeKit integration for smart home connectivity
- **Server Implementations**: Multiple XP server type support (XP130, XP230, etc.)
- **Configuration Management**: YAML-based configuration with validation

## Development

### Using PDM Scripts

The project uses PDM for dependency management with convenient scripts:

```bash
# Run all tests with coverage
pdm run test

# Run only unit tests
pdm run test-unit

# Run only integration tests
pdm run test-integration

# Run tests with HTML coverage report
pdm run test-cov

# Code quality checks
pdm run lint           # Check code with ruff
pdm run lint-fix       # Fix linting issues automatically
pdm run format         # Format code with black
pdm run format-check   # Check formatting
pdm run typecheck      # Type checking with mypy

# Run all quality checks
pdm run check

# Clean up build artifacts
pdm run clean
```

### Manual Testing Commands

```bash
# Run all tests with coverage (manual)
PYTHONPATH=src python -m pytest tests/ -v --cov=src/xp --cov-report=term-missing

# Run specific test file
PYTHONPATH=src python -m pytest tests/unit/test_models/test_event_telegram.py -v

# Run tests with coverage threshold
PYTHONPATH=src python -m pytest tests/ -v --cov=src/xp --cov-report=term-missing --cov-fail-under=90
```

### Code Quality

The project includes comprehensive tooling for code quality:

- **Testing**: pytest with 90% coverage requirement
- **Formatting**: black code formatter
- **Linting**: ruff (modern Python linter)
- **Type Checking**: mypy static type checker
- **Dead Code Detection**: vulture
- **Dependency Management**: PDM

### Project Structure

```
xp/
├── src/xp/
│   ├── api/           # FastAPI REST endpoints
│   │   ├── models/    # API data models
│   │   └── routers/   # API route handlers
│   ├── cli/           # Command-line interface
│   │   ├── commands/  # CLI command modules
│   │   └── utils/     # CLI utilities
│   ├── connection/    # Network communication
│   ├── models/        # Core data models
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── fixtures/      # Test data and fixtures
├── pyproject.toml     # Project configuration
└── pdm.lock          # Dependency lock file
```

## Requirements

### Runtime Dependencies

- **Python 3.10+** (Required)
- **click >= 8.0** - CLI framework with colored help
- **click-help-colors >= 0.9** - Colored CLI help text
- **pyyaml >= 6.0** - YAML configuration support
- **structlog >= 22.0** - Structured logging
- **fastapi >= 0.104.0** - REST API framework
- **uvicorn >= 0.24.0** - ASGI server
- **pydantic >= 2.0.0** - Data validation and serialization
- **HAP-python[QRCode] >= 5.0.0** - HomeKit integration

### Development Dependencies

- **pytest >= 7.0** - Testing framework
- **pytest-cov >= 4.0** - Coverage reporting
- **black >= 22.0** - Code formatting
- **ruff >= 0.1.0** - Modern Python linting
- **mypy >= 1.0** - Static type checking
- **vulture >= 2.14** - Dead code detection
- **httpx >= 0.24.0** - HTTP client for testing

## License

MIT License - see LICENSE file for details.

## Notice

This software is developed for **interoperability purposes only** under fair use provisions and EU Software Directive Article 6. See NOTICE.md for full details on intellectual property compliance.