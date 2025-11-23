# Conbus Export ActionTable Enhancement

## Overview

Add a new `xp conbus export actiontable` command to download action tables for devices listed in `export.yml`. This allows users to separately export action tables after capturing device metadata, providing flexibility in export workflows.

## Problem Statement

The current `xp conbus export` command captures device metadata (type, version, link number, etc.) but omits action tables. Users must separately run `xp conbus actiontable download` for each device to get complete configuration. This is:

- **Time-consuming**: Requires manual iteration over all devices
- **Error-prone**: Easy to miss devices or forget to export action tables
- **Incomplete**: Export doesn't capture full device state

## Solution

Add a new `xp conbus export actiontable` command that:

1. Reads the `export.yml` file to discover devices
2. For each device in the export file, downloads its action table using `ActionTableService`
3. Updates the `export.yml` file with action table data
4. Shows progress for each device's action table download

## Use Cases

- **Complete Backup**: Export entire system state including all programmed behaviors
- **System Migration**: Capture full configuration for transferring to new hardware
- **Documentation**: Generate comprehensive system documentation with all logic
- **Comparison**: Diff exports before/after changes to verify action table modifications

## CLI Interface

```bash
# Step 1: Export device metadata
xp conbus export

# Step 2: Download action tables for all devices in export.yml
xp conbus export actiontable
```

### Command Behavior

- Reads `export.yml` to discover devices
- Downloads action table for each device sequentially
- Updates `export.yml` with action table data
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
1. Read Export File Phase
   └─ Load export.yml using ConsonConfigLoader
   └─ Extract device list with serial numbers

2. Action Table Download Phase
  └─ For each device in export.yml:
     └─ Use ActionTableService to download
     └─ Store ActionTable in device config
     └─ Handle download errors gracefully

3. Update Export File Phase
   └─ Update ConsonModuleListConfig with action tables
   └─ Write back to export.yml
```

### Service Architecture

New `ConbusExportActionTableService`:

```
ConbusExportActionTableService (new)
├─ Dependencies
│  ├─ cli_config: CliConfig
│  ├─ reactor: Reactor
│  ├─ actiontable_serializer: ActionTableSerializer
│  ├─ telegram_service: TelegramService
│  └─ conson_config_loader: ConsonConfigLoader
├─ State
│  ├─ module_configs: List[ConsonModuleConfig] (loaded from export.yml)
│  ├─ current_device_index: int
│  ├─ actiontable_download_complete: Set[str]
│  └─ actiontable_failed: Set[str]
├─ Flow
│  ├─ start(export_file: str = "export.yml")
│  │  └─ Load export.yml using ConsonConfigLoader
│  │  └─ Extract devices with serial numbers
│  │  └─ Start sequential downloads
│  ├─ _download_next_actiontable()
│  │  └─ Get next device from module_configs
│  │  └─ Use ActionTableService.start()
│  │  └─ Register callbacks for progress/finish/error
│  ├─ _on_actiontable_finish(serial_number: str, actiontable_short: List[str])
│  │  └─ Clean semicolons from actiontable_short
│  │  └─ Update device config's action_table field
│  │  └─ Mark device as complete
│  │  └─ Download next device or finalize
│  ├─ _on_actiontable_error(serial_number: str, error: str)
│  │  └─ Log warning
│  │  └─ Mark device as failed (without action_table field)
│  │  └─ Download next device or finalize
│  └─ _finalize_export()
│     └─ Build ConsonModuleListConfig from updated module_configs
│     └─ Write back to export.yml using Pydantic serialization
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

Progress display for `xp conbus export actiontable`:

```
Loading export.yml...
Found 3 devices

Downloading action table 1/3: A12 (0020041013)...
  ✓ Action table: 42 entries

Downloading action table 2/3: A9 (1234567890)...
  ⚠ Action table: timeout (skipped)

Downloading action table 3/3: A15 (9876543210)...
  ✓ Action table: 0 entries

Export updated: export.yml (2/3 action tables downloaded)
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

New command under `xp conbus export`:

```python
@export_group.command("actiontable")
@click.option(
    "--file",
    "-f",
    "export_file",
    default="export.yml",
    help="Export file to read/update (default: export.yml)",
)
@click.pass_context
@connection_command()
def export_actiontable(ctx: click.Context, export_file: str) -> None:
    """Download action tables for devices in export file.

    Reads the specified export.yml file, downloads action tables for each
    device, and updates the file with the action table data.

    Args:
        ctx: Click context object.
        export_file: Path to export file (default: export.yml).

    Examples:
        \\b
        # Download action tables for devices in export.yml
        xp conbus export actiontable

        # Download action tables for devices in custom file
        xp conbus export actiontable --file my-export.yml
    """
    # ... implementation ...
```

### Service Changes

New `ConbusExportActionTableService` handles:
- Loading export.yml
- Sequential action table downloads
- Updating export.yml with action table data

## Performance Considerations

### Timeouts

- **Action table download timeout per device**: 10 seconds
- **Total timeout estimate**: ~10s × num_devices

For 12 devices:
- Estimated time: ~120 seconds (2 minutes)

### User Experience

Display estimated time for large installations:

```python
if device_count > 10:
    click.echo(
        f"Downloading action tables for {device_count} devices "
        f"(est. {device_count * 10}s)...",
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
- **Export behavior**: `xp conbus export` remains unchanged (metadata-only)
- **New command**: `xp conbus export actiontable` is an additive feature

## Future Enhancements

1. **Parallel downloads**: If bridge modules support multiple connections in future
2. **Selective download**: `--devices` flag to download action tables for specific devices only
3. **Action table upload**: Reverse operation to upload action tables from YAML
4. **Diff mode**: Compare action tables between exports

## References

### Existing Components

- `src/xp/services/conbus/actiontable/actiontable_download_service.py` - Action table download
- `src/xp/models/actiontable/actiontable.py` - Action table models
- `src/xp/models/homekit/homekit_conson_config.py` - ConsonModuleConfig (already has action_table field!)
- `src/xp/services/actiontable/actiontable_serializer.py` - Serialization logic
- `src/xp/loaders/conson_config_loader.py` - For loading export.yml

### Related Documentation

- `doc/conbus/Feat-Export.md` - Base export feature specification
- `doc/Quality.md` - Quality standards and testing requirements
- `doc/Coding.md` - Type safety, documentation, naming conventions

### Implementation Pattern

Follow the pattern from existing action table and export commands:
- `src/xp/cli/commands/conbus/actiontable/actiontable_download_commands.py` - CLI pattern for action tables
- `src/xp/cli/commands/conbus/export_commands.py` - CLI pattern for export commands
- Sequential processing with progress callbacks
- Error handling that doesn't fail entire operation
- Reactor and event loop management
- Load/update YAML using ConsonConfigLoader
