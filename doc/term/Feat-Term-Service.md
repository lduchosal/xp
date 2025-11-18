# Feature: Decoupling Term Interface from ConbusEventProtocol

## References

- [Architecture](../Architecture.md) - System architecture and layer separation principles
- [Coding Standards](../Coding.md) - Type safety, documentation, and naming conventions
- [Quality Management](../Quality.md) - Quality checklist and testing requirements

## Overview

Currently, the terminal interface (`ProtocolMonitorApp` and `ProtocolLogWidget`) directly interacts with `ConbusEventProtocol`, creating tight coupling between the presentation layer (TUI) and the protocol layer. This document describes the work required to introduce a service layer that encapsulates protocol operations and provides a cleaner separation of concerns.

## Current Architecture

### Direct Protocol Coupling

**File: `src/xp/term/widgets/protocol_log.py`**

```python
# Lines 15, 43, 64
from xp.services.protocol import ConbusEventProtocol

class ProtocolLogWidget(Widget):
    def __init__(self, container: Any) -> None:
        self.protocol: Optional[ConbusEventProtocol] = None

    async def on_mount(self) -> None:
        # Direct protocol resolution and signal connection
        self.protocol = self.container.resolve(ConbusEventProtocol)

        # Direct signal connections (lines 67-72)
        self.protocol.on_connection_made.connect(self._on_connection_made)
        self.protocol.on_connection_failed.connect(self._on_connection_failed)
        self.protocol.on_telegram_received.connect(self._on_telegram_received)
        self.protocol.on_telegram_sent.connect(self._on_telegram_sent)
        self.protocol.on_timeout.connect(self._on_timeout)
        self.protocol.on_failed.connect(self._on_failed)
```

### Problems with Current Design

1. **Tight Coupling**: Widget directly depends on `ConbusEventProtocol` implementation
2. **Protocol Knowledge**: Widget needs to understand protocol-specific details (IP, port, transport)
3. **Signal Management**: Widget manages low-level protocol signals directly
4. **Connection Lifecycle**: Widget handles connection state machine and async operations
5. **No Abstraction**: No interface between presentation and protocol layers
6. **Testing Difficulty**: Hard to test widget independently of real protocol

## Proposed Architecture

### Service Layer Introduction

Create a new `ProtocolMonitorService` that:
- Wraps `ConbusEventProtocol`
- Provides high-level operations for the TUI
- Manages protocol lifecycle and connection state
- Translates protocol events to domain events
- Follows the existing service pattern used in `ConbusDiscoverService` and `ConbusReceiveService`

### Ownership Model

**Service Ownership:**
- `ProtocolMonitorApp` owns the service (resolved via DI container)
- Service is injected into `ProtocolLogWidget` constructor
- App controls service lifecycle and can access it for app-level actions
- Widget receives service as dependency, doesn't resolve it directly

### Service Pattern Reference

The codebase already has established service patterns:

**Example: `ConbusDiscoverService` (lines 23-42)**
```python
class ConbusDiscoverService:
    """Service for discovering modules on Conbus servers."""

    conbus_protocol: ConbusEventProtocol
    on_progress: Signal = Signal(str)
    on_finish: Signal = Signal(DiscoveredDevice)

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        self.conbus_protocol = conbus_protocol
        # Connect to protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
```

**Example: `ConbusReceiveService` (lines 18-34)**
```python
class ConbusReceiveService:
    """Service for receiving telegrams from Conbus servers."""

    conbus_protocol: ConbusEventProtocol
    on_progress: Signal = Signal(str)
    on_finish: Signal = Signal(ConbusReceiveResponse)

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        self.conbus_protocol = conbus_protocol
        # Service handles protocol signal translation
```

## Implementation Plan

### 1. Create ProtocolMonitorService

**New file: `src/xp/services/term/protocol_monitor_service.py`**

```python
"""Protocol Monitor Service for terminal interface."""

import logging
from typing import Optional

from psygnal import Signal
from twisted.python.failure import Failure

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.term.connection_state import ConnectionState
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class TelegramDisplayEvent:
    """Event containing telegram data for display."""
    direction: str  # "RX" or "TX"
    telegram: str
    timestamp: Optional[float] = None


class ProtocolMonitorService:
    """
    Service for protocol monitoring in terminal interface.

    Wraps ConbusEventProtocol and provides high-level operations
    for the TUI without exposing protocol implementation details.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        on_connection_state_changed: Signal emitted when connection state changes.
        on_telegram_display: Signal emitted when telegram should be displayed.
        on_status_message: Signal emitted for status updates.
    """

    on_connection_state_changed: Signal = Signal(ConnectionState)
    on_telegram_display: Signal = Signal(TelegramDisplayEvent)
    on_status_message: Signal = Signal(str)

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        """Initialize the Protocol Monitor service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
        """
        self.logger = logging.getLogger(__name__)
        self.conbus_protocol = conbus_protocol
        self._connection_state = ConnectionState.DISCONNECTED
        self._state_machine = ConnectionState.create_state_machine()

        # Connect to protocol signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to protocol signals."""
        self.conbus_protocol.on_connection_made.connect(self._on_connection_made)
        self.conbus_protocol.on_connection_failed.connect(self._on_connection_failed)
        self.conbus_protocol.on_telegram_received.connect(self._on_telegram_received)
        self.conbus_protocol.on_telegram_sent.connect(self._on_telegram_sent)
        self.conbus_protocol.on_timeout.connect(self._on_timeout)
        self.conbus_protocol.on_failed.connect(self._on_failed)

    def _disconnect_signals(self) -> None:
        """Disconnect from protocol signals."""
        self.conbus_protocol.on_connection_made.disconnect(self._on_connection_made)
        self.conbus_protocol.on_connection_failed.disconnect(self._on_connection_failed)
        self.conbus_protocol.on_telegram_received.disconnect(self._on_telegram_received)
        self.conbus_protocol.on_telegram_sent.disconnect(self._on_telegram_sent)
        self.conbus_protocol.on_timeout.disconnect(self._on_timeout)
        self.conbus_protocol.on_failed.disconnect(self._on_failed)

    @property
    def connection_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._connection_state

    @property
    def server_info(self) -> str:
        """Get server connection info (IP:port)."""
        return f"{self.conbus_protocol.cli_config.ip}:{self.conbus_protocol.cli_config.port}"

    def connect(self) -> None:
        """Initiate connection to server."""
        if not self._state_machine.can_transition("connect"):
            self.logger.warning(
                f"Cannot connect: current state is {self._connection_state.value}"
            )
            return

        if self._state_machine.transition("connecting", ConnectionState.CONNECTING):
            self._connection_state = ConnectionState.CONNECTING
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connecting to {self.server_info}...")

        self.conbus_protocol.connect()

    def disconnect(self) -> None:
        """Disconnect from server."""
        if not self._state_machine.can_transition("disconnect"):
            self.logger.warning(
                f"Cannot disconnect: current state is {self._connection_state.value}"
            )
            return

        if self._state_machine.transition("disconnecting", ConnectionState.DISCONNECTING):
            self._connection_state = ConnectionState.DISCONNECTING
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit("Disconnecting...")

        self.conbus_protocol.disconnect()

        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self._connection_state = ConnectionState.DISCONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit("Disconnected")

    def send_telegram(self, name: str, telegram: str) -> None:
        """Send a raw telegram.

        Args:
            name: Display name for the telegram.
            telegram: Raw telegram string.
        """
        try:
            self.conbus_protocol.send_raw_telegram(telegram)
            self.on_status_message.emit(f"{name} sent.")
        except Exception as e:
            self.logger.error(f"Failed to send telegram: {e}")
            self.on_status_message.emit(f"Failed: {e}")

    # Protocol signal handlers

    def _on_connection_made(self) -> None:
        """Handle connection established."""
        if self._state_machine.transition("connected", ConnectionState.CONNECTED):
            self._connection_state = ConnectionState.CONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connected to {self.server_info}")

    def _on_connection_failed(self, failure: Failure) -> None:
        """Handle connection failed."""
        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self._connection_state = ConnectionState.DISCONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(failure.getErrorMessage())

    def _on_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle telegram received."""
        display_event = TelegramDisplayEvent(
            direction="RX",
            telegram=event.frame
        )
        self.on_telegram_display.emit(display_event)

    def _on_telegram_sent(self, telegram: str) -> None:
        """Handle telegram sent."""
        display_event = TelegramDisplayEvent(
            direction="TX",
            telegram=telegram
        )
        self.on_telegram_display.emit(display_event)

    def _on_timeout(self) -> None:
        """Handle timeout."""
        self.logger.debug("Timeout occurred (continuous monitoring)")

    def _on_failed(self, error: str) -> None:
        """Handle connection failed."""
        if self._state_machine.transition("failed", ConnectionState.FAILED):
            self._connection_state = ConnectionState.FAILED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Failed: {error}")

    def cleanup(self) -> None:
        """Clean up service resources."""
        self._disconnect_signals()
        if self.conbus_protocol.transport:
            self.disconnect()
```

### 2. Refactor ProtocolLogWidget

**File: `src/xp/term/widgets/protocol_log.py`**

Changes needed:

1. **Update constructor to accept service**
   - Line 34: Change signature from `__init__(self, container: Any)` to `__init__(self, service: ProtocolMonitorService)`
   - Remove `self.container = container`
   - Store `self.service = service`

2. **Replace protocol dependency with service dependency**
   - Line 15: Change import from `ConbusEventProtocol` to `ProtocolMonitorService`
   - Line 43: Remove `self.protocol: Optional[ConbusEventProtocol] = None`
   - Add `self.service: ProtocolMonitorService` (received via constructor)

3. **Simplify on_mount**
   - Lines 57-76: Remove container resolution and protocol initialization
   - Line 64: Remove `self.protocol = self.container.resolve(ConbusEventProtocol)`
   - Lines 67-72: Replace protocol signal connections with service signal connections
   - Connect to `on_connection_state_changed`, `on_telegram_display`, `on_status_message`

4. **Remove protocol-specific knowledge**
   - Lines 101, 136: Remove direct access to `self.protocol.cli_config`
   - Use `service.server_info` property instead

5. **Simplify connection management**
   - Lines 78-116: Remove `_start_connection_async()` complexity
   - Replace with simple `self.service.connect()` call

6. **Remove state machine duplication**
   - Line 46: Remove `self._state_machine` (service handles this)
   - Lines 90-94, 209-214, 225-229: Remove state transition logic
   - Use service's state instead

7. **Simplify event handlers**
   - Lines 151-171: Replace separate RX/TX handlers with single telegram display handler
   - Line 261: Replace `send_raw_telegram` with `service.send_telegram`

8. **Clean up unmount**
   - Lines 280-291: Replace manual signal disconnection with `service.cleanup()`

**Updated Constructor:**
```python
def __init__(self, service: ProtocolMonitorService) -> None:
    """Initialize the Protocol Log widget.

    Args:
        service: ProtocolMonitorService instance for protocol operations.
    """
    super().__init__()
    self.border_title = "Protocol"
    self.service = service
    self.logger = logging.getLogger(__name__)
    self.log_widget: Optional[RichLog] = None
```

**Updated on_mount:**
```python
async def on_mount(self) -> None:
    """Initialize connection when widget mounts.

    Delays connection by 0.5s to let UI render first.
    """
    # Connect to service signals
    self.service.on_connection_state_changed.connect(self._on_state_changed)
    self.service.on_telegram_display.connect(self._on_telegram_display)
    self.service.on_status_message.connect(self._on_status_message)

    # Delay connection to let UI render
    await asyncio.sleep(0.5)
    self.service.connect()
```

### 3. Refactor ProtocolMonitorApp

**File: `src/xp/term/protocol.py`**

Changes needed:

1. **Resolve service in app constructor**
   - Line 41: After `self.container = container`
   - Add `self.protocol_service = container.resolve(ProtocolMonitorService)`

2. **Inject service into widget**
   - Line 70: Change from `ProtocolLogWidget(container=self.container)`
   - To `ProtocolLogWidget(service=self.protocol_service)`

3. **Update app actions to use service**
   - Lines 82-94: `action_toggle_connection()` can access `self.protocol_service.connection_state`
   - Simplify by using service instead of checking widget state

**Updated App Constructor:**
```python
def __init__(self, container: Any) -> None:
    """Initialize the Protocol Monitor app.

    Args:
        container: ServiceContainer for resolving services.
    """
    super().__init__()
    self.container = container
    self.protocol_service = container.resolve(ProtocolMonitorService)
    self.protocol_widget: Optional[ProtocolLogWidget] = None
    self.help_menu: Optional[HelpMenuWidget] = None
    self.footer_widget: Optional[StatusFooterWidget] = None
    self.protocol_keys = self._load_protocol_keys()
```

**Updated compose method:**
```python
def compose(self) -> ComposeResult:
    """Compose the app layout with widgets.

    Yields:
        ProtocolLogWidget and Footer widgets.
    """
    with Horizontal(id="main-container"):
        self.protocol_widget = ProtocolLogWidget(service=self.protocol_service)
        yield self.protocol_widget

        # Help menu (hidden by default)
        self.help_menu = HelpMenuWidget(
            protocol_keys=self.protocol_keys, id="help-menu"
        )
        yield self.help_menu

    self.footer_widget = StatusFooterWidget(id="footer-container")
    yield self.footer_widget
```

**Simplified action_toggle_connection:**
```python
def action_toggle_connection(self) -> None:
    """Toggle connection on 'c' key press.

    Connects if disconnected/failed, disconnects if connected/connecting.
    """
    from xp.models.term.connection_state import ConnectionState

    state = self.protocol_service.connection_state
    if state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
        self.protocol_service.disconnect()
    else:
        self.protocol_service.connect()
```

### 4. Update Dependency Injection

**File: `src/xp/utils/dependencies.py`**

Register the new service as a singleton:
```python
self.container.register(
    ProtocolMonitorService,
    factory=lambda: ProtocolMonitorService(
        conbus_protocol=self.container.resolve(ConbusEventProtocol)
    ),
    scope=punq.Scope.singleton,
)
```

### 5. Update Models

**New file: `src/xp/models/term/telegram_display.py`**

Create domain models for TUI events:
```python
"""Domain models for telegram display in terminal interface."""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class TelegramDisplayEvent:
    """Event containing telegram data for display in TUI.

    Attributes:
        direction: Direction of telegram ("RX" for received, "TX" for transmitted).
        telegram: Formatted telegram string.
        timestamp: Optional timestamp of the event.
    """

    direction: Literal["RX", "TX"]
    telegram: str
    timestamp: Optional[float] = None
```

## Benefits of This Refactoring

### Separation of Concerns

- **App**: Owns service, controls lifecycle, handles app-level actions
- **Widget**: Receives service, handles UI rendering and user interaction
- **Service**: Manages protocol lifecycle, connection state, event translation
- **Protocol**: Low-level network communication

### Clear Ownership

- App resolves service from DI container (singleton)
- App injects service into widget constructor (dependency injection)
- Widget doesn't resolve dependencies, receives them
- App can access service for app-level operations (toggle connection, etc.)

### Improved Testability

- Widget can be tested with mock service
- Service can be tested independently of TUI
- Protocol remains isolated

### Code Reusability

- Service can be reused in other contexts (web UI, API)
- Multiple widgets can share same service instance
- Business logic centralized in service

### Maintainability

- Changes to protocol don't require widget changes
- Clearer responsibilities and boundaries
- Easier to understand and modify

### Consistency

- Follows existing service pattern (`ConbusDiscoverService`, `ConbusReceiveService`)
- Consistent with codebase architecture
- Predictable structure for developers

## Migration Path

### Phase 1: Create Service Layer
1. Create `ProtocolMonitorService` class
2. Create `TelegramDisplayEvent` model
3. Add service registration to DI container (`src/xp/utils/dependencies.py`)
4. Add unit tests for service

### Phase 2: Refactor App
1. Update `ProtocolMonitorApp` constructor to resolve service
2. Update `compose()` to inject service into widget
3. Simplify app actions to use service directly
4. App now owns the service

### Phase 3: Refactor Widget
1. Update `ProtocolLogWidget` constructor to accept service parameter
2. Remove `container` dependency
3. Remove protocol-specific code and state machine
4. Simplify signal handling to use service signals
5. Update widget tests to inject mock service

### Phase 4: Integration & Cleanup
1. Integration testing of app → service → protocol flow
2. Remove unused imports
3. Update documentation
4. Verify no regressions

## Files to Modify

### New Files
- `src/xp/services/term/__init__.py`
- `src/xp/services/term/protocol_monitor_service.py`
- `src/xp/models/term/telegram_display.py`
- `tests/unit/test_services/test_protocol_monitor_service.py`

### Modified Files
- `src/xp/term/widgets/protocol_log.py` (major refactor - constructor change, remove container)
- `src/xp/term/protocol.py` (moderate refactor - resolve service, inject into widget)
- `src/xp/utils/dependencies.py` (register new service)

### Unchanged Files
- `src/xp/services/protocol/conbus_event_protocol.py` (no changes needed)
- `src/xp/models/term/connection_state.py` (no changes needed)

## Estimated Complexity

- **Service Implementation**: ~200-250 lines
- **Widget Refactoring**: ~100 lines removed, ~30 lines modified
- **Tests**: ~150-200 lines
- **Total LOC**: ~300-350 new/modified

## Risks and Considerations

### Potential Issues

1. **Signal Timing**: Ensure service signals fire at correct times
2. **State Synchronization**: Widget and service state must stay in sync
3. **Error Handling**: Service must properly translate protocol errors
4. **Cleanup**: Ensure proper signal disconnection and resource cleanup

### Mitigation

1. Comprehensive unit tests for service
2. Integration tests for widget + service
3. Careful review of signal connection/disconnection
4. Manual testing of all connection scenarios

## Future Enhancements

Once service layer is established:

1. **Multiple Protocol Support**: Service could support different protocol types
2. **Session Recording**: Service could record sessions for replay
3. **Filtering**: Service could filter telegrams before display
4. **Statistics**: Service could gather connection/telegram statistics
5. **Reconnection**: Service could implement auto-reconnect logic

## Implementation Guidelines

### Architecture Compliance

This refactoring follows the principles outlined in [Architecture.md](../Architecture.md):

1. **Layer Separation**: Maintains CLI → Services → Protocol → Connection hierarchy
2. **Dependency Injection**: Service registered in ServiceContainer (punq) as singleton
3. **Event-Driven**: Uses psygnal signals for event propagation
4. **Type Safety**: Full type hints with Pydantic models where appropriate

### Coding Standards

Implementation must adhere to [Coding.md](../Coding.md):

- **Type Safety**: Complete type hints for all methods, no `Any` unless necessary
- **Documentation**: Docstrings for all public classes and methods (Args, Returns)
- **Naming**: `ProtocolMonitorService` (PascalCase), `send_telegram` (snake_case)
- **Imports**: Absolute imports only, properly ordered (stdlib → third-party → local)

### Quality Requirements

Before merging, all checks from [Quality.md](../Quality.md) must pass:

- `pdm run typecheck` - Mypy strict mode compliance
- `pdm run flake8` - Code quality and documentation checks
- `pdm test-quick` - All tests passing
- `pdm format` - Black formatting applied
- `pdm lint` - Ruff linting passed
- Minimum 75% test coverage maintained

## Conclusion

This refactoring introduces a clean service layer between the terminal interface and protocol implementation, following established patterns in the codebase. It improves separation of concerns, testability, and maintainability while setting up a foundation for future enhancements.

The work is well-scoped and follows the existing architecture, making it a natural evolution of the codebase structure.