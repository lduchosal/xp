# Download ActionTable Workflow - Implementation Plan

## Goal

Refactor `ActionTableDownloadService` to inherit from [python-statemachine](https://pypi.org/project/python-statemachine/) `StateMachine` class.

## Checklist

### Phase 1: Add Dependency

- [ ] Add `python-statemachine = "^2.5.0"` to `pyproject.toml`
- [ ] Run `pdm install`

### Phase 2: Refactor Service

- [ ] Add `from statemachine import StateMachine, State` import
- [ ] Change class to `class ActionTableDownloadService(StateMachine):`
- [ ] Define 9 states as class attributes using `State()`
- [ ] Define all transitions using `State.to()`
- [ ] Call `super().__init__()` at end of `__init__`
- [ ] Implement lifecycle hooks (`on_enter_*`, `on_exit_*`, `after_*`)

### Phase 3: Update Event Handlers

- [ ] Replace state checks with `self.<state>.is_active`
- [ ] Replace transitions with `self.<event>()` calls
- [ ] Handle `TransitionNotAllowed` exceptions
- [ ] Ensure existing signal handlers work with state machine

### Phase 4: Tests

- [ ] Test initial state is `idle`
- [ ] Test `connection_made` transitions `idle → receiving`
- [ ] Test `timeout` transitions `receiving → resetting`
- [ ] Test chunk flow: `waiting_data → receiving_chunk → waiting_data`
- [ ] Test EOF flow: `waiting_data → processing_eof`
- [ ] Test invalid transitions raise `TransitionNotAllowed`
- [ ] Test full download flow end-to-end
- [ ] Test lifecycle hooks access service attributes

### Phase 5: Quality

- [ ] Run `sh publish.sh --quality`
- [ ] Fix any issues

### Phase 6: Cleanup

- [ ] Remove `xp/utils/state_machine.py` if unused elsewhere
