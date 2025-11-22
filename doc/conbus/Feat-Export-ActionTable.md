# Conbus Export ActionTable Enhancement

## Overview

Extend `xp conbus export` to automatically download action tables from each discovered device. This provides a complete snapshot of both device configuration and programmed behavior in a single operation.

## Problem Statement

The current `xp conbus export` command captures device metadata (type, version, link number, etc.) but omits action tables. Users must separately run `xp conbus actiontable download` for each device to get complete configuration. This is:

- **Time-consuming**: Requires manual iteration over all devices
- **Error-prone**: Easy to miss devices or forget to export action tables
- **Incomplete**: Export doesn't capture full device state

## Solution

Enhance `xp conbus export` to always download action tables:

1. Performs standard device discovery and metadata export
2. For each device, automatically downloads its action table using `ActionTableService`
3. Includes action table data in the exported YAML
4. Shows progress for both metadata and action table downloads

## Use Cases

- **Complete Backup**: Export entire system state including all programmed behaviors
- **System Migration**: Capture full configuration for transferring to new hardware
- **Documentation**: Generate comprehensive system documentation with all logic
- **Comparison**: Diff exports before/after changes to verify action table modifications

## CLI Interface

```bash
# Export complete configuration (metadata + action tables)
xp conbus export
```

### Command Behavior

- **Always downloads action tables** for all discovered devices
- No flags needed - complete export by default
- Gracefully handles devices without action tables (omitted from YAML)
- Errors downloading action tables don't fail the entire export

### Output

Export file format remains `export.yml` with optional `action_table` field per device:

```yaml
- name: A12
  serial_number: "0020041013"
  module_type: XP130
  module_type_code: 13
  link_number: 12
  module_number: 1
  sw_version: XP130_V0.10.04
  hw_version: XP130_HW_Rev B
  auto_report_status: AA
  action_table:  # Automatically downloaded if device has one
    - XP20 10 0 > 0 OFF
    - XP20 10 0 > 1 OFF
    - XP20 10 0 > 2 OFF
    - XP20 10 8 > 0 ON
    - XP20 10 8 > 1 ON
    - XP20 10 8 > 2 ON
    - CP20 0 0 > 0 OFF
    - CP20 0 0 > 1 OFF
    - CP20 0 8 > 0 ON
    - CP20 0 8 > 1 ON

- name: A9
  serial_number: "1234567890"
  module_type: XP24
  module_type_code: 7
  link_number: 9
  # ... (no action_table if device has none or download failed)
```

## Implementation Approach

### High-Level Flow

```
1. Discovery Phase (existing)
   └─ Send DISCOVERY telegram
   └─ Collect device serial numbers

2. Metadata Query Phase (existing)
   └─ For each device: query 7 datapoints
   └─ Store in device_configs

3. Action Table Download Phase (NEW)
  └─ For each device:
     └─ Use ActionTableService to download
     └─ Store ActionTable in device_configs
     └─ Handle download errors gracefully

4. Finalization Phase (existing + enhanced)
   └─ Build ConsonModuleListConfig
   └─ Include action_table field if present
   └─ Write to export.yml
```

### Service Architecture Enhancement

Extend `ConbusExportService` with action table support:

```
ConbusExportService (enhanced)
├─ Dependencies (enhanced)
│  ├─ conbus_protocol: ConbusEventProtocol (existing)
│  └─ actiontable_service: ActionTableService (existing)
├─ State (enhanced)
│  ├─ discovered_devices: List[str] (existing)
│  ├─ device_configs: Dict[str, Dict[str, Any]] (existing)
│  ├─ device_datapoints_received: Dict[str, Set[str]] (existing)
│  ├─ actiontable_download_queue: List[str] (NEW)
│  └─ actiontable_download_complete: Set[str] (NEW)
├─ Enhanced Flow
│  ├─ _check_device_complete() (modified)
│  │  └─ If all 7 datapoints received:
│  │     └─ Start action table download for this device
│  ├─ _download_actiontable(serial_number: str) (NEW)
│  │  └─ Use ActionTableService.start()
│  │  └─ Register callbacks for progress/finish/error
│  ├─ _on_actiontable_progress(serial_number: str, message: str) (NEW)
│  │  └─ Emit progress updates
│  ├─ _on_actiontable_finish(serial_number: str, actiontable_short: List[str]) (NEW)
│  │  └─ Clean semicolons from actiontable_short
│  │  └─ Store in device_configs[serial_number]['action_table']
│  │  └─ Mark device as complete
│  │  └─ Check if all downloads complete
│  ├─ _on_actiontable_error(serial_number: str, error: str) (NEW)
│  │  └─ Log warning
│  │  └─ Mark device as complete (without action_table field)
│  │  └─ Continue with remaining devices
│  └─ _finalize_export() (modified)
│     └─ Wait for all action table downloads to complete
│     └─ Build ConsonModuleListConfig including action_table fields
│     └─ Write to export.yml using Pydantic serialization
```

### Sequential vs Parallel Downloads

**Decision**: Use **sequential** action table downloads (one at a time)

**Rationale**:
- XP bridge modules (XP130, XP230) accept only **one TCP connection at a time**
- ActionTableService creates its own TCP connection per download
- Cannot download from multiple devices simultaneously
- ConbusEventProtocol (used for metadata) is separate from ActionTableService connections

**Implementation**:
```python
# After all metadata collected, download action tables sequentially
for serial_number in discovered_devices:
    self._download_actiontable(serial_number)
    # Wait for download to complete before next device
```

### Integration with ActionTableService

Reuse existing `ActionTableService` for each device:

```python
def _download_actiontable(self, serial_number: str) -> None:
    """Download action table for a device.

    Args:
        serial_number: Device serial number.
    """
    self.logger.info(f"Downloading action table for {serial_number}")

    # Create service instance (uses separate TCP connection)
    actiontable_service = ActionTableService(
        cli_config=self.cli_config,
        reactor=self.reactor,
        actiontable_serializer=self.actiontable_serializer,
        telegram_service=self.telegram_service,
    )

    # Start download with callbacks
    actiontable_service.start(
        serial_number=serial_number,
        progress_callback=lambda msg: self._on_actiontable_progress(serial_number, msg),
        error_callback=lambda err: self._on_actiontable_error(serial_number, err),
        finish_callback=lambda at, _, short: self._on_actiontable_finish(serial_number, short),
        timeout_seconds=10.0,
    )
```

### Action Table Format Conversion

The `ActionTableService` provides action tables in two formats:

1. **ActionTable object** (structured) - Contains `ActionTableEntry` objects
2. **Short format** (list[str]) - Human-readable strings from `format_decoded_output()`

For `conson.yml` compatibility, use the **short format** with semicolon removal:

```python
def _on_actiontable_finish(
    self, serial_number: str, actiontable_short: list[str]
) -> None:
    """Handle action table download completion.

    Args:
        serial_number: Device serial number.
        actiontable_short: Formatted action table strings (with semicolons).
    """
    # Remove semicolons for conson.yml format
    # Input:  ["CP20 0 0 > 1 OFF;", "XP20 10 8 > 0 ON;"]
    # Output: ["CP20 0 0 > 1 OFF", "XP20 10 8 > 0 ON"]
    cleaned_entries = [line.rstrip(";") for line in actiontable_short]

    # Store in device config dict
    self.device_configs[serial_number]["action_table"] = cleaned_entries

    # Mark download complete
    self.actiontable_download_complete.add(serial_number)

    # Emit progress
    count = len(cleaned_entries)
    click.echo(f"  ✓ Action table: {count} entries")

    # Check if all downloads complete
    self._check_all_actiontables_complete()
```

**Format Examples:**

ActionTableSerializer output (with semicolon):
```
CP20 0 0 > 1 OFF;
CP20 0 0 > 1 ~ON;
XP20 10 8 > 0 ON 5;
```

Conson.yml format (without semicolon):
```yaml
action_table:
  - CP20 0 0 > 1 OFF
  - CP20 0 0 > 1 ~ON
  - XP20 10 8 > 0 ON 5
```

### Error Handling

Action table download errors should **not** fail the entire export:

| Error Scenario | Behavior |
|----------------|----------|
| Action table download timeout | Log warning, omit `action_table` field for device, continue |
| Action table empty | Include empty `action_table: []` in YAML |
| Connection refused | Log warning, omit `action_table` field, continue |
| Invalid action table data | Log warning, omit `action_table` field, continue |
| Device doesn't support action tables | Silent skip, no `action_table` field |

**Export Status**:
- `export_status: "OK"` - All metadata and requested action tables downloaded
- `export_status: "PARTIAL_ACTIONTABLE"` - Metadata complete, some action tables failed
- `export_status: "FAILED_TIMEOUT"` - Some metadata incomplete (existing)

### Progress Reporting

Enhanced progress display:

```
Discovering devices... (timeout: 5s)
Found 3 devices

Querying device 1/3: 0020041013...
  ✓ Module type: XP130 (13)
  ✓ Link number: 12
  ✓ Software version: XP130_V0.10.04
  ✓ Downloading action table...
  ✓ Action table: 42 entries

Querying device 2/3: 1234567890...
  ✓ Module type: XP24 (7)
  ✓ Link number: 9
  ✓ Software version: XP24_V0.34.03
  ✓ Downloading action table...
  ⚠ Action table: timeout (skipped)

Querying device 3/3: 9876543210...
  ✓ Module type: XP33 (11)
  ✓ Link number: 15
  ✓ Software version: XP33_V1.02.01
  ✓ Downloading action table...
  ✓ Action table: empty

Export complete: export.yml (3 devices, 2/3 action tables)
```

## Data Models

### Enhanced ConbusExportResponse

```python
@dataclass
class ConbusExportResponse:
    """Export operation result."""
    success: bool
    config: Optional[ConsonModuleListConfig] = None
    device_count: int = 0
    actiontable_count: int = 0  # NEW: Number of action tables downloaded
    actiontable_failed: int = 0  # NEW: Number of action table downloads that failed
    output_file: str = "export.yml"
    export_status: str = "OK"  # OK, PARTIAL_ACTIONTABLE, FAILED_TIMEOUT, etc.
    error: Optional[str] = None
    sent_telegrams: List[str] = field(default_factory=list)
    received_telegrams: List[str] = field(default_factory=list)
```

### ConsonModuleConfig Enhancement

Existing model already supports optional `action_table` field:

```python
@dataclass
class ConsonModuleConfig:
    """Conson module configuration."""
    name: str
    serial_number: str
    module_type: Optional[str] = None
    module_type_code: Optional[int] = None
    link_number: Optional[int] = None
    module_number: Optional[int] = None
    sw_version: Optional[str] = None
    hw_version: Optional[str] = None
    auto_report_status: Optional[str] = None
    action_table: Optional[List[ActionTableEntry]] = None  # Already exists!
    # ... other optional fields ...
```

**No model changes needed** - just populate the existing field!

## Testing Strategy

### Unit Tests

**New Tests**:
- Test `_download_actiontable()` calls ActionTableService correctly
- Test `_on_actiontable_finish()` stores ActionTable in device_configs
- Test `_on_actiontable_error()` marks device complete without action table
- Test sequential download queueing (one at a time)
- Test export includes action_table field when present
- Test export omits action_table field when download fails
- Test export_status values (OK, PARTIAL_ACTIONTABLE)

**Modified Tests**:
- Update `test_finalize_export_writes_file()` to verify action_table serialization
- Add `--with-actiontable` flag test cases

### Integration Tests

- Test full export with action tables using XP server emulators
- Verify YAML round-trip with action tables
- Test multi-device export with mixed action table scenarios (some fail, some succeed)
- Test action table download timeout handling

## CLI Integration

### Command Definition

The CLI command remains unchanged - action tables are downloaded automatically:

```python
@conbus.command("export")
@click.pass_context
@connection_command()
def export_conbus_config(ctx: click.Context) -> None:
    """Export Conbus device configuration to YAML file.

    Discovers all devices on the Conbus network and queries their configuration
    datapoints (including action tables) to generate a complete export.yml file
    in conson.yml format.

    Args:
        ctx: Click context object.

    Examples:
        \\b
        # Export complete configuration
        xp conbus export
    """
    # ... implementation ...
    # Action tables are always downloaded
```

### Service Changes

No configuration needed - `ConbusExportService` always downloads action tables after collecting metadata.

## Performance Considerations

### Timeouts

- **Metadata query timeout**: 5 seconds (existing)
- **Action table download timeout per device**: 10 seconds (new)
- **Total timeout estimate**: 5s + (10s × num_devices)

For 12 devices:
- Without action tables: ~5 seconds
- With action tables: ~125 seconds (2+ minutes)

### User Experience

Add warning for large installations:

```python
if device_count > 10:
    click.echo(
        f"⚠ Downloading action tables for {device_count} devices "
        f"(est. {device_count * 10}s)",
        err=True,
    )
```

## Dependencies

**New Dependencies**:
- `ActionTableService` (existing) - For downloading action tables
- `ActionTableSerializer` (existing) - For deserializing action table data
- `ActionTable` (existing) - Action table model
- `ActionTableEntry` (existing) - Action table entry model

**No new external packages required**

## Backward Compatibility

- **YAML format**: Existing exports remain valid (action_table field is optional)
- **Model compatibility**: ConsonModuleConfig already supports action_table field
- **Export behavior change**: Now includes action tables by default (was metadata-only)
- **Performance impact**: Export takes longer (~10s per device for action tables)

## Future Enhancements

1. **Parallel downloads**: If bridge modules support multiple connections in future
2. **Selective download**: `--devices` flag to download action tables for specific devices only
3. **Action table upload**: Reverse operation to upload action tables from YAML
4. **Diff mode**: Compare action tables between exports

## References

### Existing Components

- `src/xp/services/conbus/conbus_export_service.py` - Base export service
- `src/xp/services/conbus/actiontable/actiontable_download_service.py` - Action table download
- `src/xp/models/actiontable/actiontable.py` - Action table models
- `src/xp/models/homekit/homekit_conson_config.py` - ConsonModuleConfig (already has action_table field!)
- `src/xp/services/actiontable/actiontable_serializer.py` - Serialization logic

### Related Documentation

- `doc/conbus/Feat-Export.md` - Base export feature specification
- `doc/Quality.md` - Quality standards and testing requirements
- `doc/Coding.md` - Type safety, documentation, naming conventions

### Implementation Pattern

Follow the pattern from existing action table commands:
- `src/xp/cli/commands/conbus/actiontable/actiontable_download_commands.py` - CLI pattern
- Sequential processing with progress callbacks
- Error handling that doesn't fail entire operation
- Reactor and event loop management
