# Download ActionTable Workflow Specification

## Overview

Downloads actiontable from XP module via Conbus protocol using a signal-driven state machine powered by [python-statemachine](https://pypi.org/project/python-statemachine/).

## States

| State           | Description                                           |
|-----------------|-------------------------------------------------------|
| IDLE            | Initial state, waiting for connection                 |
| RECEIVING       | Listening for telegrams, filtering relevant responses |
| RESETTING       | Timeout occurred, preparing error status              |
| WAITING_OK      | Sent error status, awaiting ACK/NAK                   |
| REQUESTING      | Ready to send download request                        |
| WAITING_DATA    | Awaiting actiontable chunk or EOF                     |
| RECEIVING_CHUNK | Processing received actiontable data                  |
| PROCESSING_EOF  | Received EOF, deserializing actiontable               |
| COMPLETED       | Download finished successfully                        |

## State Transitions

### Phase 1: Connection & Reset Handshake

```
IDLE → RECEIVING           on_connection_made
RECEIVING → RECEIVING      on_telegram_received (filter non-relevant)
RECEIVING → RESETTING      on_timeout
RESETTING → WAITING_OK     send_datapoint_error_status
WAITING_OK → RECEIVING     nak_received | on_timeout (retry)
WAITING_OK → REQUESTING    ack_received
```

### Phase 2: Download

```
REQUESTING → WAITING_DATA       send_download_actiontable (F11D)
WAITING_DATA → RECEIVING_CHUNK  actiontable_received (F7D)
WAITING_DATA → WAITING_DATA     on_telegram_received (filter)
RECEIVING_CHUNK → WAITING_DATA  send_ack (F8D)
WAITING_DATA → PROCESSING_EOF   eof_received (F6D)
```

### Phase 3: Finalization

```
PROCESSING_EOF → RECEIVING      on_finish (emit actiontable)
RECEIVING → RESETTING           on_timeout
RESETTING → WAITING_OK          send_datapoint_error_status
WAITING_OK → RECEIVING          nak_received | on_timeout
WAITING_OK → COMPLETED          ack_received
```

## Signals

| Signal | Payload | Description |
|--------|---------|-------------|
| on_progress | str | Emitted per chunk received |
| on_error | str | Emitted on failure |
| on_finish | (ActionTable, dict, list[str]) | Emitted on successful completion |

## Protocol Messages

| Function | Code | Direction | Purpose |
|----------|------|-----------|---------|
| DOWNLOAD_ACTIONTABLE | F11D | TX | Request download |
| ACTIONTABLE | F7D | RX | Chunk data |
| ACK | F8D | TX | Acknowledge chunk |
| EOF | F6D | RX | End of transmission |
| ERROR_STATUS | - | TX | Reset datapoint error |

## Telegram Filtering

Only process telegrams where:
- `checksum_valid == True`
- `telegram_type == REPLY`
- `serial_number == target_serial`
- `system_function in (ACTIONTABLE, EOF)`

## State Machine Definition (python-statemachine)

The service inherits from `StateMachine`, making the service itself the state machine. This provides direct access to lifecycle hooks and cleaner code.

```python
from statemachine import StateMachine, State


class ActionTableDownloadService(StateMachine):
    """Downloads actiontable via Conbus protocol.

    Inherits from StateMachine - the service IS the state machine.
    """

    # States
    idle = State(initial=True)
    receiving = State()
    resetting = State()
    waiting_ok = State()
    requesting = State()
    waiting_data = State()
    receiving_chunk = State()
    processing_eof = State()
    completed = State(final=True)

    # Phase 1: Connection & Reset Handshake
    connection_made = idle.to(receiving)
    timeout = receiving.to(resetting)
    send_error_status = resetting.to(waiting_ok)
    nak_received = waiting_ok.to(receiving)
    ack_received = waiting_ok.to(requesting)
    ack_final = waiting_ok.to(completed)

    # Phase 2: Download
    send_download = requesting.to(waiting_data)
    actiontable_received = waiting_data.to(receiving_chunk)
    send_ack = receiving_chunk.to(waiting_data)
    eof_received = waiting_data.to(processing_eof)

    # Phase 3: Finalization
    finish = processing_eof.to(receiving)

    def __init__(self, conbus: Conbus, serial: str) -> None:
        self._conbus = conbus
        self._serial = serial
        super().__init__()  # Initialize state machine

    # Lifecycle hooks - direct access to service attributes
    def on_enter_receiving(self) -> None:
        """Start listening for telegrams."""
        self._conbus.subscribe(self._on_telegram)

    def on_exit_receiving(self) -> None:
        """Stop listening for telegrams."""
        self._conbus.unsubscribe(self._on_telegram)

    def after_actiontable_received(self) -> None:
        """Process received chunk and emit progress."""
        self.on_progress.emit(f"Received chunk {self._chunk_count}")

    def after_eof_received(self) -> None:
        """Deserialize actiontable and emit result."""
        actiontable = self._deserialize()
        self.on_finish.emit(actiontable)
```

## Design: Inheritance vs Composition

| Aspect | Inheritance (chosen) | Composition |
|--------|---------------------|-------------|
| Access pattern | `self.idle.is_active` | `self._machine.idle.is_active` |
| Event trigger | `self.connection_made()` | `self._machine.connection_made()` |
| Lifecycle hooks | Direct methods on service | Require delegation |
| Service attributes | Direct `self._conbus` access | Need to pass context |

Inheritance is preferred because:
- The service IS the workflow - they're conceptually the same thing
- Lifecycle hooks have direct access to service attributes (`self._conbus`, `self._serial`)
- Less boilerplate code
- Cleaner, more readable implementation

## Callback Hooks

Use python-statemachine naming conventions for lifecycle hooks:

| Hook Pattern        | Example                      | Purpose                    |
|---------------------|------------------------------|----------------------------|
| `on_enter_<state>`  | `on_enter_receiving`         | Called when entering state |
| `on_exit_<state>`   | `on_exit_waiting_data`       | Called when leaving state  |
| `before_<event>`    | `before_send_download`       | Called before transition   |
| `after_<event>`     | `after_actiontable_received` | Called after transition    |

## Error Handling

- Timeout → send error status → retry on NAK
- Invalid checksum → ignore telegram
- Wrong serial → ignore telegram
- Connection failure → emit on_error
