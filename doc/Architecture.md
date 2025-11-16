# Architecture

## Overview
XP is a CLI toolkit for CONSON XP Protocol operations with HomeKit integration. Event-driven architecture with dependency injection.

## System Purpose
- **Protocol**: TCP communication with XP130/XP230 servers (CONSON XP Protocol)
- **Operations**: Telegram parsing, device discovery, real-time control
- **Integration**: Apple HomeKit bridge for smart home
- **Architecture**: Layered, event-driven, type-safe (Pydantic + strict mypy)

## Core Principles
1. **Dependency Injection**: All services registered in ServiceContainer (punq)
2. **Event-Driven**: Central EventBus (bubus) for protocol/HomeKit communication
3. **Type Safety**: Pydantic models, mypy strict mode (no untyped defs)
4. **Layer Separation**: CLI → Services → Protocol → Connection
5. **Test Coverage**: Minimum 75% (pytest with strict config)

## Layer Architecture

### Layer 1: CLI
**Location**: `src/xp/cli/`
- **CLI**: Click-based commands, resolve services from ServiceContainer via context
- **Rule**: NO business logic, only input validation and output formatting
- **Entry**: `cli/main.py` initializes ServiceContainer, registers command groups
- **Validation**: Click types handle all parameter validation (ranges, enums, custom types)

### Layer 2: Services
**Location**: `src/xp/services/`
- **Telegram Services**: Low-level telegram operations (parse, generate, validate)
- **Conbus Services**: High-level device operations (discover, scan, control)
- **HomeKit Services**: HAP-python integration, event handling
- **Server Services**: XP protocol emulators
- **Pattern**: All services injected via ServiceContainer, use EventBus for communication

### Layer 3: Protocol + Events
**Location**: `src/xp/services/protocol/`, `src/xp/models/protocol/`
- **TelegramProtocol**: Twisted Protocol for TCP (asyncio reactor)
- **TelegramFactory**: Connection lifecycle management
- **EventBus**: Central dispatcher (bubus), 500 event history
- **Events**: Protocol events (connection, telegrams), HomeKit events, datapoint events

### Layer 4: Connection
**Location**: Connection pool, socket managers
- **ConbusConnectionPool**: Manages TCP connections to XP servers
- **ConbusSocketConnectionManager**: Low-level socket operations
- **Config**: Loaded from `cli.yml` (host, port, timeout)

### Layer 5: Models
**Location**: `src/xp/models/`
- **Pydantic models** for all data structures
- `telegram/`: Event, System, Reply telegram types
- `conbus/`: Operation requests/responses
- `homekit/`: Configuration and accessory models
- `protocol/`: Event definitions (BaseEvent from bubus)

## Actual Project Structure
```
src/xp/
├── cli/                    # Click CLI commands
│   ├── main.py            # Entry point, ServiceContainer init
│   └── commands/          # Command groups (conbus, telegram, homekit, etc.)
├── services/              # Business logic layer
│   ├── telegram/          # Low-level telegram operations
│   ├── conbus/            # High-level device operations
│   ├── homekit/           # HomeKit integration
│   ├── protocol/          # TelegramProtocol, TelegramFactory
│   └── server/            # XP emulators (XP20, XP24, XP33, etc.)
├── models/                # Pydantic data models
│   ├── telegram/          # Telegram types (Event, System, Reply)
│   ├── conbus/            # Conbus operation models
│   ├── homekit/           # HomeKit config and accessories
│   └── protocol/          # Event definitions (bubus BaseEvent)
├── connection/            # TCP/socket exceptions
└── utils/                 # Dependency injection (ServiceContainer)

tests/
├── unit/                  # Service/model unit tests
└── integration/           # End-to-end integration tests
```

## Key Components

### 1. ServiceContainer (`src/xp/utils/dependencies.py`)
Central DI container (punq) managing all service lifecycle and dependencies:
```python
# Initialize container (CLI does this automatically)
container = ServiceContainer(
    config_path="cli.yml",
    homekit_config_path="homekit.yml",
    conson_config_path="conson.yml"
)

# Resolve service (automatic dependency injection)
service = container.container.resolve(ConbusEventRawService)
```

**Registration**: All services registered in `_register_services()` with factory lambdas
**Scope**: Singleton by default (shared across requests)
**Pattern**: Constructor injection - dependencies resolved automatically

### 2. EventBus (bubus)
Event-driven communication between protocol and services:
- **Protocol Events**: `ConnectionMadeEvent`, `TelegramReceivedEvent`, `ModuleDiscoveredEvent`
- **HomeKit Events**: `LightBulbSetOnEvent`, `ReadDatapointEvent`, `SendActionEvent`
- **Pattern**: Services subscribe to events, dispatch new events

### 3. Protocol Layer
- **TelegramProtocol**: Twisted Protocol handling TCP I/O
- **TelegramFactory**: Creates protocol instances, manages connection lifecycle
- **TelegramService**: Stateless telegram parsing/generation

### 4. Telegram Format
```
<TYPE SERIAL PAYLOAD CHECKSUM>
Event:  <E14L00I02MAK>              # Button press
System: <S0020012521F02D18FN>       # Query device
Reply:  <R0020012521F02D18+26,0§CIL> # Device response
```

### 5. Configuration Files
- `cli.yml`: Conbus connection (host, port, timeout)
- `homekit.yml`: HomeKit bridge configuration
- `conson.yml`: Module definitions
- `server.yml`: Emulator settings

## Implementation Patterns

### Adding a New Service
1. Create service in `src/xp/services/`
2. Register in `ServiceContainer._register_services()`
3. Inject dependencies via constructor
4. Use EventBus for async communication

### Adding a New Command
1. Create command in `src/xp/cli/commands/`
2. Use Click types for validation:
   - **Range**: `@click.argument("port", type=click.IntRange(0, 99))`
   - **Enum**: Custom type like `MODULE_TYPE` (see `cli/utils/module_type_choice.py`)
   - **Pattern**: Validation errors thrown before function execution
3. Register in `cli/main.py` or parent command group
4. Resolve service from context: `ctx.obj["container"].container.resolve(ServiceClass)`
5. No business logic in command - delegate to service

**Example**:
```python
@click.command()
@click.argument("module_type", type=MODULE_TYPE)  # Custom enum validator
@click.argument("link", type=click.IntRange(0, 99))  # Range validator
@click.pass_context
def my_command(ctx: click.Context, module_type: int, link: int) -> None:
    service = ctx.obj["container"].container.resolve(MyService)
    service.run(module_type, link)
```

### Adding a New Event
1. Extend `BaseEvent` in `models/protocol/conbus_protocol.py`
2. Dispatch via `event_bus.dispatch(YourEvent(...))`
3. Subscribe in service: `@event_bus.on(YourEvent)`

### Testing Pattern
- **Unit Tests**: Mock dependencies, inject via constructor
- **Integration Tests**: Use real ServiceContainer with test config
- **Coverage**: Minimum 75%, run `pdm test-cov`
- **Quick Tests**: `pdm test-quick` (quiet mode, no coverage)

## Logging

### Overview
Centralized logging via `LoggerService` with YAML configuration, rotating file output, and per-module log levels.

### Components
**Location**: `src/xp/utils/logging.py`, `src/xp/models/conbus/conbus_logger_config.py`

- **LoggerService**: Configures Python logging (console + rotating file handlers)
- **LoggingConfig** (Pydantic): Configuration model with defaults
- **ConbusLoggerConfig**: YAML loader wrapper

### Configuration
```yaml
log:
  path: "log"                    # Log directory
  default_level: "DEBUG"         # Root logger level
  levels:                        # Per-module overrides
    xp: DEBUG
    xp.services.homekit: WARNING
    xp.services.server: WARNING
  max_bytes: 1048576              # 1MB rotation
  backup_count: 365               # Keep 365 backups
  log_format: "%(asctime)s - [%(threadName)s-%(thread)d] - %(levelname)s - %(name)s - %(message)s"
  date_format: "%H:%M:%S"
```

### Setup
```python
# Automatic setup via CLI initialization
logger_config = ConbusLoggerConfig.from_yaml("logger.yml")
logger_service = LoggerService(logger_config)
logger_service.setup()
```

### Features
- **Console Logging**: StreamHandler with configurable format
- **File Logging**: RotatingFileHandler (1MB default, 365 backups)
- **Module-Level Control**: Override levels per namespace (e.g., suppress HomeKit verbosity)
- **Thread-Safe**: Includes thread name/ID in default format
- **Graceful Fallback**: Continues without file logging if path inaccessible

