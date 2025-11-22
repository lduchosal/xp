# Conbus Export Service - Pydantic Refactoring

## Overview

Refactor `ConbusExportService` to use `ConsonModuleConfig` Pydantic models directly instead of building dictionaries. This improves type safety, reduces code complexity, and eliminates duplicate state tracking.

## Problem Statement

Current implementation in `ConbusExportService` uses dictionaries for device state:

```python
# Current implementation
self.device_configs: dict[str, dict[str, Any]] = {}
self.device_datapoints_received: dict[str, set[str]] = {}
```

**Issues:**
- **No type safety**: Dictionary values are `Any`, no validation
- **Duplicate tracking**: Need separate dict to track which datapoints received
- **Manual serialization**: Must manually build dicts for YAML export
- **Error-prone**: Easy to typo field names, miss fields, or use wrong types
- **Harder to maintain**: Changes require updating multiple places

## Solution

Use `ConsonModuleConfig` Pydantic model directly:

```python
# Refactored implementation
self.device_configs: dict[str, ConsonModuleConfig] = {}
# No device_datapoints_received needed - check model fields!
```

## Benefits

### 1. Type Safety
- Pydantic validates field types automatically
- IDE autocomplete for field names
- Catch errors at assignment time, not serialization time

### 2. Simpler State Management
- Single source of truth (the model)
- No separate tracking dictionaries
- Check completion by inspecting model fields

### 3. Cleaner Code
- No manual dictionary building
- Immutable updates with `model.copy(update={...})`
- Direct serialization with `model_dump()`

### 4. Better Maintainability
- Model changes propagate automatically
- Field renames caught by type checker
- Clear schema definition

## Implementation Changes

### State Variables

**Before:**
```python
def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
    self.discovered_devices: list[str] = []
    self.device_configs: dict[str, dict[str, Any]] = {}
    self.device_datapoints_received: dict[str, set[str]] = {}
```

**After:**
```python
def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
    self.discovered_devices: list[str] = []
    self.device_configs: dict[str, ConsonModuleConfig] = {}
    # No device_datapoints_received needed!
```

### Discovery Response Handling

**Before:**
```python
def _handle_discovery_response(self, serial_number: str) -> None:
    self.discovered_devices.append(serial_number)
    self.device_configs[serial_number] = {"serial_number": serial_number}
    self.device_datapoints_received[serial_number] = set()
    # Send queries...
```

**After:**
```python
def _handle_discovery_response(self, serial_number: str) -> None:
    self.discovered_devices.append(serial_number)

    # Create ConsonModuleConfig with placeholder values for required fields
    module = ConsonModuleConfig(
        name="UNKNOWN",  # Will be updated when link_number arrives
        serial_number=serial_number,
        module_type="UNKNOWN",  # Required field
        module_type_code=0,  # Required field
        link_number=0,  # Required field
    )

    self.device_configs[serial_number] = module
    # Send queries...
```

### Storing Datapoint Values

**Before:**
```python
def _store_datapoint_value(
    self, serial_number: str, datapoint: DataPointType, value: str
) -> None:
    config = self.device_configs[serial_number]

    if datapoint == DataPointType.MODULE_TYPE:
        config["module_type"] = value
    elif datapoint == DataPointType.MODULE_TYPE_CODE:
        try:
            config["module_type_code"] = int(value)
        except ValueError:
            self.logger.warning(f"Invalid module_type_code: {value}")
    # ... etc
```

**After:**
```python
def _store_datapoint_value(
    self, serial_number: str, datapoint: DataPointType, value: str
) -> None:
    module = self.device_configs[serial_number]

    # Use Pydantic's copy with update for immutable updates
    if datapoint == DataPointType.MODULE_TYPE:
        self.device_configs[serial_number] = module.copy(
            update={"module_type": value}
        )
    elif datapoint == DataPointType.MODULE_TYPE_CODE:
        try:
            code = int(value)
            self.device_configs[serial_number] = module.copy(
                update={"module_type_code": code}
            )
        except ValueError:
            self.logger.warning(f"Invalid module_type_code: {value}")
    elif datapoint == DataPointType.LINK_NUMBER:
        try:
            link = int(value)
            # Update both link_number and name
            self.device_configs[serial_number] = module.copy(
                update={
                    "link_number": link,
                    "name": f"A{link}",
                }
            )
        except ValueError:
            self.logger.warning(f"Invalid link_number: {value}")
    # ... etc
```

**Note**: Pydantic will validate types automatically, raising `ValidationError` for invalid data.

### Checking Device Completion

**Before:**
```python
def _check_device_complete(self, serial_number: str) -> None:
    received = self.device_datapoints_received[serial_number]
    expected = {dp.value for dp in self.DATAPOINT_SEQUENCE}

    if received == expected:
        # Device is complete
        config = self.device_configs[serial_number]
        # Build ConsonModuleConfig...
        module_config = ConsonModuleConfig(**config)
        self.on_device_exported.emit(module_config)
```

**After:**
```python
def _check_device_complete(self, serial_number: str) -> None:
    module = self.device_configs[serial_number]

    # Check if all required fields are present and valid
    required_fields = [
        module.module_type not in ("UNKNOWN", None, ""),
        module.module_type_code is not None and module.module_type_code > 0,
        module.link_number is not None and module.link_number > 0,
        module.sw_version is not None,
        module.hw_version is not None,
        module.auto_report_status is not None,
        module.module_number is not None,
    ]

    if all(required_fields):
        # Device is complete - already a valid ConsonModuleConfig!
        self.on_device_exported.emit(module)
```

### Finalizing Export

**Before:**
```python
def _finalize_export(self) -> None:
    modules = []
    for serial_number in self.discovered_devices:
        config = self.device_configs[serial_number].copy()
        try:
            # Add name field
            if "name" not in config:
                link_number = config.get("link_number", 0)
                config["name"] = f"A{link_number}"

            module_config = ConsonModuleConfig(**config)
            modules.append(module_config)
        except Exception as e:
            self.logger.warning(f"Partial device {serial_number}: {e}")

    # Sort and build list
    modules.sort(key=lambda m: m.link_number if m.link_number else 999)
    module_list = ConsonModuleListConfig(root=modules)
```

**After:**
```python
def _finalize_export(self) -> None:
    # Convert dict values to list (already ConsonModuleConfig instances!)
    modules = list(self.device_configs.values())

    # Sort by link_number
    modules.sort(key=lambda m: m.link_number if m.link_number else 999)

    # Build list config
    module_list = ConsonModuleListConfig(root=modules)
```

### Context Manager Reset

**Before:**
```python
def __enter__(self) -> "ConbusExportService":
    self.discovered_devices = []
    self.device_configs = {}
    self.device_datapoints_received = {}
    self.export_result = ConbusExportResponse(success=False)
    self.export_status = "OK"
    self._finalized = False
    return self
```

**After:**
```python
def __enter__(self) -> "ConbusExportService":
    self.discovered_devices = []
    self.device_configs = {}  # No device_datapoints_received!
    self.export_result = ConbusExportResponse(success=False)
    self.export_status = "OK"
    self._finalized = False
    return self
```

## Migration Strategy

### Phase 1: Update Type Annotations (No Behavior Change)
```python
# Change type hints but keep dict operations
self.device_configs: dict[str, ConsonModuleConfig] = {}
```

### Phase 2: Refactor Discovery Response
- Create `ConsonModuleConfig` instances in `_handle_discovery_response()`
- Keep using `device_datapoints_received` for now

### Phase 3: Refactor Datapoint Storage
- Update `_store_datapoint_value()` to use `model.copy(update={...})`
- Validate with existing tests

### Phase 4: Remove Tracking Dictionary
- Update `_check_device_complete()` to check model fields
- Remove `device_datapoints_received` entirely

### Phase 5: Simplify Finalization
- Remove manual `ConsonModuleConfig(**config)` construction
- Use `list(device_configs.values())` directly

## Testing Strategy

### Unit Tests to Update

1. **Test device initialization**
   - Verify `ConsonModuleConfig` created with placeholder values
   - Check required fields have defaults

2. **Test datapoint storage**
   - Verify `copy(update={...})` creates new instances
   - Test type validation (invalid values raise errors)

3. **Test completion detection**
   - Verify required fields check logic
   - Test partial devices (some fields missing)

4. **Test finalization**
   - Verify modules are already `ConsonModuleConfig` instances
   - No manual dict-to-model conversion needed

### Integration Tests

- Full export with real devices
- Verify YAML output unchanged
- Test round-trip: export → load → validate

## Validation

### Type Checking
```bash
pdm run typecheck
# Should pass with no errors after refactoring
```

### Existing Tests
```bash
pdm run test tests/unit/test_services/test_conbus_export_service.py
# All tests should still pass
```

## Expected Improvements

### Code Metrics

- **Lines of code**: -50 lines (remove duplicate tracking)
- **Type coverage**: 100% (all fields typed)
- **Validation**: Automatic (Pydantic handles it)

### Performance

- **Negligible impact**: `copy(update={...})` is fast
- **Memory**: Slightly lower (no duplicate tracking dict)

### Maintainability

- **Field changes**: Update model once, propagates everywhere
- **Type errors**: Caught at development time
- **Readability**: Clear schema, no magic strings

## Risks and Mitigation

### Risk: Pydantic Validation Errors

**Issue**: Invalid data might raise `ValidationError`
**Mitigation**: Wrap in try/except, log warnings, continue processing other devices

### Risk: Required Field Defaults

**Issue**: Must provide defaults for required fields during discovery
**Mitigation**: Use placeholder values ("UNKNOWN", 0) that will be updated

### Risk: Immutability Overhead

**Issue**: `copy(update={...})` creates new instances
**Mitigation**: Negligible performance impact, benefit outweighs cost

## Future Enhancements

1. **Action Table Integration**: Add `action_table: Optional[List[str]]` field (already exists!)
2. **Partial Export Handling**: Use Pydantic's `exclude_unset=True` for partial devices
3. **Validation Rules**: Add custom validators for field constraints (e.g., link_number range)

## References

### Pydantic Documentation
- [Model Copy](https://docs.pydantic.dev/latest/concepts/models/#model-copy)
- [Model Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)

### Project Files
- `src/xp/models/homekit/homekit_conson_config.py` - ConsonModuleConfig model
- `src/xp/services/conbus/conbus_export_service.py` - Current implementation
- `tests/unit/test_services/test_conbus_export_service.py` - Tests to update

### Related Specifications
- `doc/conbus/Feat-Export.md` - Original export feature
- `doc/conbus/Feat-Export-ActionTable.md` - Action table enhancement (will benefit from this refactor)
