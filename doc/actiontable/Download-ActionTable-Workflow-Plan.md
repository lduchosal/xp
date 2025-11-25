# Download ActionTable Workflow - Implementation Plan

## Goal

Refactor `ActionTableDownloadService` to use explicit state machine from `xp/utils/state_machine.py`.

## Current State

- `ActionTableDownloadService` uses implicit state via signal handlers
- `StateMachine` utility exists but is not used
- Workflow diagram defines 9 states, current implementation has none

## Tasks

### 1. Define State Enum

File: `src/xp/services/conbus/actiontable/actiontable_download_state.py`

```python
class ActionTableDownloadState(str, Enum):
    IDLE = "IDLE"
    RECEIVING = "RECEIVING"
    RESETTING = "RESETTING"
    WAITING_OK = "WAITING_OK"
    REQUESTING = "REQUESTING"
    WAITING_DATA = "WAITING_DATA"
    RECEIVING_CHUNK = "RECEIVING_CHUNK"
    PROCESSING_EOF = "PROCESSING_EOF"
    COMPLETED = "COMPLETED"
```

### 2. Integrate StateMachine

File: `src/xp/services/conbus/actiontable/actiontable_download_service.py`

- Add `StateMachine` instance with `IDLE` as initial state
- Define valid transitions per workflow spec
- Guard signal handlers with state checks
- Transition state on events

### 3. Define Transitions

```
Action                    Valid Sources              Target
─────────────────────────────────────────────────────────────
on_connection_made        {IDLE}                     RECEIVING
on_telegram_received      {RECEIVING, WAITING_DATA}  (self)
on_timeout                {RECEIVING}                RESETTING
send_error_status         {RESETTING}                WAITING_OK
nak_received              {WAITING_OK}               RECEIVING
ack_received              {WAITING_OK}               REQUESTING
send_download             {REQUESTING}               WAITING_DATA
actiontable_received      {WAITING_DATA}             RECEIVING_CHUNK
send_ack                  {RECEIVING_CHUNK}          WAITING_DATA
eof_received              {WAITING_DATA}             PROCESSING_EOF
on_finish                 {PROCESSING_EOF}           RECEIVING
ack_final                 {WAITING_OK}               COMPLETED
```

### 4. Update Signal Handlers

| Handler | Add State Check | Transition To |
|---------|-----------------|---------------|
| `connection_made` | IDLE | RECEIVING |
| `telegram_received` | RECEIVING, WAITING_DATA | context-dependent |
| `timeout` | RECEIVING | RESETTING |

### 5. Tests

File: `tests/unit/test_services/test_actiontable_download_service.py`

- Test state transitions
- Test invalid transition rejection
- Test state after each signal

## Files Changed

| File | Change |
|------|--------|
| `actiontable_download_state.py` | New - state enum |
| `actiontable_download_service.py` | Modify - add state machine |
| `test_actiontable_download_service.py` | Modify - add state tests |

## Dependencies

- `xp/utils/state_machine.py` (existing)

## Implementation Checklist

### Phase 1: State Enum

- [ ] Create `src/xp/services/conbus/actiontable/actiontable_download_state.py`
- [ ] Define `ActionTableDownloadState(str, Enum)` with 9 states
- [ ] Export from `__init__.py`

### Phase 2: Integrate StateMachine

- [ ] Import `StateMachine` from `xp.utils.state_machine`
- [ ] Import `ActionTableDownloadState`
- [ ] Add `self.state_machine = StateMachine(ActionTableDownloadState.IDLE)` in `__init__`
- [ ] Define all transitions using `define_transition()`

### Phase 3: Update Handlers

- [ ] `connection_made`: check state is IDLE, transition to RECEIVING
- [ ] `telegram_received`: check state, branch logic by current state
- [ ] `timeout`: check state is RECEIVING, transition to RESETTING
- [ ] Add `_handle_actiontable_chunk()`: transition WAITING_DATA → RECEIVING_CHUNK → WAITING_DATA
- [ ] Add `_handle_eof()`: transition WAITING_DATA → PROCESSING_EOF → RECEIVING
- [ ] Reset state to IDLE in `__enter__`

### Phase 4: Tests

- [ ] Test initial state is IDLE
- [ ] Test `connection_made` transitions IDLE → RECEIVING
- [ ] Test `timeout` transitions RECEIVING → RESETTING
- [ ] Test chunk flow: WAITING_DATA → RECEIVING_CHUNK → WAITING_DATA
- [ ] Test EOF flow: WAITING_DATA → PROCESSING_EOF
- [ ] Test invalid transitions are rejected

### Phase 5: Quality

- [ ] Run `sh publish.sh --quality`
- [ ] Fix any issues
