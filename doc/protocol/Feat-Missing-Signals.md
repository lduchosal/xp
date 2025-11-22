# Missing Signal Connections - Analysis Report

## Status: 1 Critical Issue Remaining

## Fixed Issues ✅

### 1. ActionTableService - Signals NOW DEFINED ✅

**File**: `src/xp/services/conbus/actiontable/actiontable_download_service.py`

**Status**: ✅ **FIXED** - Signals are now properly defined

**Signals Defined**:
- `on_progress: Signal = Signal(str)` (line 25)
- `on_error: Signal = Signal(str)` (line 26)
- `on_finish: Signal = Signal(object)` (line 27)

**CLI Connections**: All properly connected in `conbus_actiontable_commands.py`

---

## Remaining Critical Issues

### WriteConfigService - Missing CLI Connections ❌

**File**: `src/xp/services/conbus/write_config_service.py`

**Signal Defined**: `on_finish: Signal = Signal(ConbusWriteConfigResponse)` (line 33)

**CLI Files Missing Connections**:

#### a) conbus_linknumber_commands.py ❌
- **Function**: `set_linknumber_command` (lines 40-62)
- **Missing**: `service.on_finish.connect(on_finish)`
- **Missing**: `service.start_reactor()` call
- **Current**: Only calls `service.write_config()` without signal connection

#### b) conbus_modulenumber_commands.py ❌
- **Function**: `set_modulenumber_command` (lines 40-62)
- **Missing**: `service.on_finish.connect(on_finish)`
- **Missing**: `service.start_reactor()` call

#### c) conbus_lightlevel_commands.py ❌
- **Functions**: Multiple (set/on/off lightlevel commands)
- **Missing**: Signal connections in all functions

#### d) conbus_autoreport_commands.py ❌
- **Function**: `set_autoreport_command` (lines 40-110)
- **Missing**: `service.on_finish.connect(on_finish)`
- **Missing**: `service.start_reactor()` call

**Required Fix Pattern**:
```python
def on_finish(response: ConbusWriteConfigResponse) -> None:
    click.echo(json.dumps(response.to_dict(), indent=2))
    service.stop_reactor()

with service:
    service.on_finish.connect(on_finish)
    service.write_config(...)
    service.start_reactor()
```

---

## Services Fully Migrated ✅

### 1. ConbusRawService ✅
- Signals: `on_progress`, `on_finish`
- CLI: `conbus_raw_commands.py` - All connected

### 2. ConbusCustomService ✅
- Signals: `on_finish`
- CLI: `conbus_custom_commands.py` - Connected

### 3. ConbusScanService ✅
- Signals: `on_progress`, `on_finish`
- CLI: `conbus_scan_commands.py` - All connected

### 4. ConbusDatapointQueryAllService ✅
- Signals: `on_progress`, `on_finish`
- CLI: `conbus_datapoint_commands.py` - All connected

### 5. ConbusOutputService ✅
- Signals: `on_finish`
- CLI: `conbus_output_commands.py` - Connected in both commands

### 6. ConbusBlinkAllService ✅
- Signals: `on_progress`, `on_finish`
- CLI: `conbus_blink_commands.py` - All connected

### 7. ConbusBlinkService ✅
- Signals: `on_finish`
- CLI: `conbus_blink_commands.py` - Connected in both commands

### 8. MsActionTableService ✅
- Signals: `on_progress`, `on_error`, `on_finish`
- CLI: `conbus_msactiontable_commands.py` - All connected

### 9. ActionTableService ✅ (JUST FIXED)
- Signals: `on_progress`, `on_error`, `on_finish`
- CLI: `conbus_actiontable_commands.py` - All connected

### 10. ActionTableUploadService ✅
- Signals: `on_progress`, `on_error`, `on_finish`
- CLI: `conbus_actiontable_commands.py` - All connected

### 11. ConbusDatapointService ✅
- Signals: `on_finish`
- CLI: `conbus_datapoint_commands.py` - Connected

---

## Summary

**Total Services Analyzed**: 12

**Status**:
- ✅ Fully Migrated: 11 services
- ❌ Missing CLI Connections: 1 service (WriteConfigService)

**WriteConfigService Impact**:
- 4+ CLI commands NOT connecting to signals
- Commands will likely fail or hang without signal connections
- Must be fixed for proper operation

**Priority**:
- **HIGH**: Fix WriteConfigService CLI connections in all 4+ commands

**Git Commits Referenced**:
- a62dc87 - ConbusBlinkAllService migration
- b027640 - ConbusBlinkService migration
- e7a7970 - ConbusBlinkService migration
- 383d23c - ConbusEventProtocol refactor
