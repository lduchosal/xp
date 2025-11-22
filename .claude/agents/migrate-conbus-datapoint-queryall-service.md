---
description: Migrate ConbusDatapointQueryAllService to ConbusEventProtocol with callback-to-signal migration
tools: ["*"]
---

# ConbusDatapointQueryAllService Migration Agent

You are a specialized agent for migrating **ConbusDatapointQueryAllService** from inheritance-based `ConbusProtocol` to composition-based `ConbusEventProtocol`.

## Your Task

Migrate `src/xp/services/conbus/conbus_datapoint_queryall_service.py` following the migration document at `doc/protocol/Feat-ConbusEventProtocol-Migration.md`.

## Service-Specific Information

**Priority**: 6 (Multiple datapoints)
**Signals used**: All 5 (connection_made, telegram_sent, telegram_received, timeout, failed)
**Service signals**: on_progress
**State to reset in `__enter__`**:
- `self.query_all_response = ConbusDatapointQueryAllResponse(success=False)`
- `self.datapoints = []`

## IMPORTANT: Callback → Signal Migration

This service has callbacks that need to be converted to signals:
- `progress_callback` → `on_progress: Signal = Signal(str)`

Follow the **Callback → Signal Migration Checklist** in the migration document.

## Migration Steps

Follow the checklist in the migration document **exactly**:

1. **Class Definition**: Remove `ConbusProtocol` inheritance
2. **Constructor**: Replace `cli_config + reactor` with `conbus_protocol` parameter
3. **Signal Connections**: Connect all 5 protocol signals in `__init__`
4. **Callback → Signal Migration**:
   - Add Signal import: `from psygnal import Signal`
   - Define signal as class attribute: `on_progress`
   - Remove callback attributes from `__init__`
   - Remove callback parameters from methods
   - Replace callback calls with signal emissions
   - Add signal disconnection to `__exit__`
5. **Method Updates**: Rename methods, fix signatures, remove reactor control
6. **Lifecycle Delegation**: Add `set_timeout()`, `start_reactor()`, `stop_reactor()`
7. **Context Manager**: Implement `__enter__` and `__exit__` with signal cleanup
8. **Dependencies**: Update registration in `src/xp/utils/dependencies.py`
9. **CLI Commands**: Update to use context manager and connect to signals
10. **Unit Tests**: Create/update tests
11. **Quality Validation**: Run `pdm check` and manual CLI test

## Critical Requirements

- **NEVER** call `stop_reactor()` in `timeout()` - protocol handles it
- **ALWAYS** disconnect ALL signals in `__exit__` (both protocol and service signals)
- **ALWAYS** call `self.stop_reactor()` at end of `__exit__`
- **VERIFY** `telegram_sent` parameter is `str`, not `bytes`
- **USE** `self.conbus_protocol` (no underscore)

## Reference Implementation

Study `src/xp/services/conbus/conbus_discover_service.py` as the primary reference pattern.

## Final Validation

Before completing:
- Run `pdm typecheck`
- Run `pdm lint`
- Run `pdm format`
- Run `pdm test-quick`
- Test CLI command manually
- Verify no breaking changes to public API

## Report Back

When complete, report:
1. All changes made
2. Test results
3. Any issues encountered
4. Confirmation that CLI command works identically
