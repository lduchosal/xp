# Architecture

## Overview
XP is a CLI/API toolkit for CONSON XP Protocol operations with HomeKit integration. Event-driven architecture with dependency injection.

## System Purpose
- **Protocol**: TCP communication with XP130/XP230 servers (CONSON XP Protocol)
- **Operations**: Telegram parsing, device discovery, real-time control
- **Integration**: Apple HomeKit bridge for smart home
- **Architecture**: Layered, event-driven, type-safe (Pydantic + strict mypy)

## Core Principles
1. **Dependency Injection**: All services registered in ServiceContainer (punq)
2. **Event-Driven**: Central EventBus (bubus) for protocol/HomeKit communication
3. **Type Safety**: Pydantic models, mypy strict mode (no untyped defs)
4. **Layer Separation**: CLI/API → Services → Protocol → Connection
5. **Test Coverage**: Minimum 75% (pytest with strict config)

## Layer Architecture

### Layer 1: CLI/API
**Location**: `src/xp/cli/`, `src/xp/api/`
- **CLI**: Click-based commands, resolve services from ServiceContainer via context
- **API**: FastAPI routers, uses same service layer
- **Rule**: NO business logic, only input validation and output formatting
- **Entry**: `cli/main.py` initializes ServiceContainer, registers command groups

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
├── api/                    # FastAPI REST endpoints
│   └── routers/           # API route handlers
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
Central DI container managing all service lifecycle and dependencies:
```python
container = ServiceContainer(
    config_path="cli.yml",
    homekit_config_path="homekit.yml",
    conson_config_path="conson.yml"
)
service = container.container.resolve(ConbusProtocol)
```

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
2. Register in `cli/main.py`
3. Resolve service from context: `ctx.obj["container"].container.resolve(ServiceClass)`
4. No business logic in command - delegate to service

### Adding a New Event
1. Extend `BaseEvent` in `models/protocol/conbus_protocol.py`
2. Dispatch via `event_bus.dispatch(YourEvent(...))`
3. Subscribe in service: `@event_bus.on(YourEvent)`

### Testing Pattern
- **Unit Tests**: Mock dependencies, inject via constructor
- **Integration Tests**: Use real ServiceContainer with test config
- **Coverage**: Minimum 75%, run `pdm test-cov`
- **Quick Tests**: `pdm test-quick` (quiet mode, no coverage)

