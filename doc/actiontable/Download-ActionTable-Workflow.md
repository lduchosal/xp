# Download ActionTable Workflow Specification

## Overview

Downloads actiontable from XP module via Conbus protocol using a signal-driven state machine.

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

## Error Handling

- Timeout → send error status → retry on NAK
- Invalid checksum → ignore telegram
- Wrong serial → ignore telegram
- Connection failure → emit on_error
