# Callbacks to Signals Migration Checklist

## Status: 4 services have remaining callbacks (6/10 complete)

## Services Fully Migrated ✅
- ConbusRawService
- ConbusCustomService
- ConbusScanService
- ConbusDatapointQueryAllService
- ConbusOutputService
- MsActionTableService

## Services with Remaining Callbacks

### 1. ConbusDatapointService

**File**: `src/xp/services/conbus/conbus_datapoint_service.py`

**Remaining Callback**:
- [ ] Remove `datapoint_finished_callback: Optional[Callable[[ConbusDatapointResponse], None]]` attribute (line 59-61)
- [ ] Remove `finish_callback` parameter from `query_datapoint` method (line 177)
- [ ] Remove callback storage in `query_datapoint` (line 191)
- [ ] Remove callback invocations in `succeed` (line 147-148) and `failed` (line 170-171)
- [ ] Update CLI: `src/xp/cli/commands/conbus/conbus_datapoint_commands.py` to remove callback parameter

**Note**: `on_finish` signal already exists and works correctly - callback is redundant

---

### 2. WriteConfigService

**File**: `src/xp/services/conbus/write_config_service.py`

**Remaining Callback**:
- [ ] Remove `write_config_finished_callback: Optional[Callable[[ConbusWriteConfigResponse], None]]` attribute (line 51-53)
- [ ] Remove `finish_callback` parameter from `write_config` method (line 193)
- [ ] Remove callback storage in `write_config` (line 211)
- [ ] Remove callback invocation in `finished` (line 185-186)
- [ ] Update CLI commands (4 files):
  - `src/xp/cli/commands/conbus/conbus_modulenumber_commands.py`
  - `src/xp/cli/commands/conbus/conbus_linknumber_commands.py`
  - `src/xp/cli/commands/conbus/conbus_lightlevel_commands.py`
  - `src/xp/cli/commands/conbus/conbus_autoreport_commands.py`

**Note**: `on_finish` signal already exists and works correctly - callback is redundant

---

### 3. ActionTableService (actiontable_download_service)

**File**: `src/xp/services/conbus/actiontable/actiontable_download_service.py`

**Callbacks to Migrate**:

#### a) progress_callback
- [ ] Remove `progress_callback: Optional[Callable[[str], None]]` attribute (line 40)
- [ ] Add `on_progress: Signal = Signal(str)` class attribute
- [ ] Remove `progress_callback` parameter from `start` method (line 144)
- [ ] Replace `if self.progress_callback: self.progress_callback(message)` with `self.on_progress.emit(message)` (line 106-107)
- [ ] Add `self.on_progress.disconnect()` in `__exit__`

#### b) error_callback
- [ ] Remove `error_callback: Optional[Callable[[str], None]]` attribute (line 41)
- [ ] Add `on_error: Signal = Signal(str)` class attribute
- [ ] Remove `error_callback` parameter from `start` method (line 145)
- [ ] Replace `if self.error_callback: self.error_callback(message)` with `self.on_error.emit(message)` (line 138-139)
- [ ] Add `self.on_error.disconnect()` in `__exit__`

#### c) finish_callback
- [ ] Remove `finish_callback: Optional[Callable[[ActionTable, Dict[str, Any], list[str]], None]]` attribute (line 42-44)
- [ ] Add `on_finish: Signal = Signal(object)` class attribute (emits tuple: (ActionTable, Dict, list))
- [ ] Remove `finish_callback` parameter from `start` method (line 146)
- [ ] Replace `if self.finish_callback: self.finish_callback(...)` with `self.on_finish.emit((action_table, telegram_dict, sent_telegrams))` (line 123-124)
- [ ] Add `self.on_finish.disconnect()` in `__exit__`

#### CLI Update
- [ ] Update `src/xp/cli/commands/conbus/conbus_actiontable_commands.py`:
  - Connect to signals: `service.on_progress.connect(...)`, `service.on_error.connect(...)`, `service.on_finish.connect(...)`
  - Remove callback parameters from `service.start()`
  - Add `service.stop_reactor()` in `on_finish` handler

---

### 4. ActionTableUploadService

**File**: `src/xp/services/conbus/actiontable/actiontable_upload_service.py`

**Callbacks to Migrate**:

#### a) progress_callback
- [ ] Remove `progress_callback: Optional[Callable[[str], None]]` attribute (line 42)
- [ ] Add `on_progress: Signal = Signal(str)` class attribute
- [ ] Remove `progress_callback` parameter from `start` method (line 161)
- [ ] Replace `if self.progress_callback: self.progress_callback(message)` with `self.on_progress.emit(message)` (line 124-125)
- [ ] Add `self.on_progress.disconnect()` in `__exit__`

#### b) error_callback
- [ ] Remove `error_callback: Optional[Callable[[str], None]]` attribute (line 43)
- [ ] Add `on_error: Signal = Signal(str)` class attribute
- [ ] Remove `error_callback` parameter from `start` method (line 162)
- [ ] Replace `if self.error_callback: self.error_callback(message)` with `self.on_error.emit(message)` (line 155-156)
- [ ] Add `self.on_error.disconnect()` in `__exit__`

#### c) success_callback
- [ ] Remove `success_callback: Optional[Callable[[], None]]` attribute (line 44)
- [ ] Add `on_finish: Signal = Signal(bool)` class attribute (emit True on success)
- [ ] Remove `success_callback` parameter from `start` method (line 163)
- [ ] Replace `if self.success_callback: self.success_callback()` with `self.on_finish.emit(True)` (line 135-136)
- [ ] Add `self.on_finish.disconnect()` in `__exit__`

#### CLI Update
- [ ] Update `src/xp/cli/commands/conbus/conbus_actiontable_commands.py`:
  - Connect to signals: `service.on_progress.connect(...)`, `service.on_error.connect(...)`, `service.on_finish.connect(...)`
  - Remove callback parameters from `service.start()`
  - Add `service.stop_reactor()` in `on_finish` handler

---

## Migration Priority

1. **ConbusDatapointService** - Simple removal (signal exists)
2. **WriteConfigService** - Simple removal (signal exists)
3. **ActionTableService** - 3 callbacks to convert
4. **ActionTableUploadService** - 3 callbacks to convert

## Validation

After each service:
- [ ] Run `pdm typecheck`
- [ ] Run `pdm lint`
- [ ] Run `pdm format`
- [ ] Run `pdm test-quick`
- [ ] Verify CLI commands work identically
