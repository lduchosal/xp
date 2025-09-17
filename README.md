# XP CLI Tool

A Python command-line interface for parsing and analyzing remote console bus telegrams, module types, and checksum operations.

## Features

- **Telegram Parsing**: Parse event, system, and reply telegrams from remote console bus devices
- **Module Type Management**: Search and retrieve information about module types
- **Checksum Operations**: Calculate and validate checksums with multiple algorithms
- **JSON Output**: All commands support both human-readable and JSON output formats
- **Comprehensive Testing**: 90%+ test coverage with unit and integration tests

## Installation

### From Source
```bash
git clone <repository-url>
cd xp
pip install -e .
```

### Development Installation
```bash
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

### JSON Output

Add `--json-output` or `-j` to any command for JSON formatted output:

```bash
xp telegram parse "<E14L00I02MAK>" --json-output
xp module info 14 -j
xp checksum calculate "E14L00I02M" -j
```

## Architecture

The project follows a layered architecture with clear separation of concerns:

- **CLI Layer** (`cli/`): Command-line interface and input validation
- **Services Layer** (`services/`): Business logic and operations
- **Models Layer** (`models/`): Data structures and response models
- **Utils Layer** (`utils/`): Utility functions and helpers

## Development

### Running Tests

```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=src/xp --cov-report=term-missing

# Run specific test file
python -m pytest tests/unit/test_models/test_event_telegram.py -v

# Run tests with coverage threshold
python -m pytest tests/ -v --cov=src/xp --cov-report=term-missing --cov-fail-under=90
```

### Code Quality

The project includes configuration for:

- **Testing**: pytest with 90% coverage requirement
- **Formatting**: black code formatter
- **Type Checking**: mypy static type checker
- **Linting**: flake8

### Project Structure

```
xp/
├── src/xp/
│   ├── cli/           # Command-line interface
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── fixtures/      # Test data and fixtures
└── requirements*.txt  # Dependencies
```

## Requirements

- Python 3.8+
- click >= 8.0
- pyyaml >= 6.0
- structlog >= 22.0

### Development Requirements

- pytest >= 7.0
- pytest-cov >= 4.0
- black >= 22.0
- flake8 >= 5.0
- mypy >= 1.0

## License

MIT License - see LICENSE file for details.