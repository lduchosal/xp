# Feature: Move Responsibilities To BaseServerService

## Overview

The current XP device server services (`xp24_server_service.py`, `xp20_server_service.py`, `xp130_server_service.py`, `xp230_server_service.py`, `xp33_server_service.py`) contain significant code duplication. This feature specification outlines the consolidation of common responsibilities into the `BaseServerService` class to reduce duplication, improve maintainability, and ensure consistent behavior across all device types.

## Current State Analysis

### Duplicate Code Patterns Identified

#### 1. **Discovery Response Generation** (100% identical across all services)
- **Files**: All 5 XP services
- **Method**: `generate_discovery_response()`
- **Pattern**: 
  ```python
  def generate_discovery_response(self) -> str:
      data_part = f"R{self.serial_number}F01D"
      checksum = calculate_checksum(data_part)
      telegram = f"<{data_part}{checksum}>"
      self.logger.debug(f"Generated {device_type} discovery response: {telegram}")
      return telegram
  ```

#### 2. **Version Response Generation** (95% identical)
- **Files**: All 5 XP services
- **Method**: `generate_version_response(request: SystemTelegram)`
- **Pattern**:
  ```python
  def generate_version_response(self, request: SystemTelegram) -> Optional[str]:
      if (request.system_function == SystemFunction.READ_DATAPOINT and
          request.data_point_id == DataPointType.VERSION):
          data_part = f"R{self.serial_number}F02D02{self.firmware_version}"
          checksum = calculate_checksum(data_part)
          telegram = f"<{data_part}{checksum}>"
          self.logger.debug(f"Generated {device_type} version response: {telegram}")
          return telegram
      return None
  ```

#### 3. **Status Response Generation** (90% identical)
- **Files**: All 5 XP services  
- **Method**: `generate_status_response(request: SystemTelegram)`
- **Variations**: XP33 uses `DataPointType.STATUS_QUERY` instead of `DataPointType.STATUS`
- **Pattern**:
  ```python
  def generate_status_response(self, request: SystemTelegram) -> Optional[str]:
      if (request.system_function == SystemFunction.READ_DATAPOINT and
          request.data_point_id == DataPointType.NONE):  # or STATUS_QUERY for XP33
          data_part = f"R{self.serial_number}F02D00{self.device_status}"
          checksum = calculate_checksum(data_part)
          telegram = f"<{data_part}{checksum}>"
          self.logger.debug(f"Generated {device_type} status response: {telegram}")
          return telegram
      return None
  ```

#### 4. **Link Number Response Generation** (95% identical)
- **Files**: All 5 XP services
- **Method**: `generate_link_number_response(request: SystemTelegram)`
- **Pattern**:
  ```python
  def generate_link_number_response(self, request: SystemTelegram) -> Optional[str]:
      if (request.system_function == SystemFunction.READ_DATAPOINT and
          request.data_point_id == DataPointType.LINK_NUMBER):
          link_hex = f"{self.link_number:02X}"
          data_part = f"R{self.serial_number}F02D04{link_hex}"
          checksum = calculate_checksum(data_part)
          telegram = f"<{data_part}{checksum}>"
          self.logger.debug(f"Generated {device_type} link number response: {telegram}")
          return telegram
      return None
  ```

#### 5. **Link Number Setting** (100% identical)
- **Files**: All 5 XP services
- **Method**: `set_link_number(request: SystemTelegram, new_link_number: int)`
- **Pattern**:
  ```python
  def set_link_number(self, request: SystemTelegram, new_link_number: int) -> Optional[str]:
      if (request.system_function == SystemFunction.WRITE_CONFIG and
          request.data_point_id == DataPointType.LINK_NUMBER):
          self.link_number = new_link_number
          data_part = f"R{self.serial_number}F18D"
          checksum = calculate_checksum(data_part)
          telegram = f"<{data_part}{checksum}>"
          self.logger.info(f"{device_type} link number set to {new_link_number}")
          return telegram
      return None
  ```

#### 6. **Common Device Initialization Pattern** (90% similar)
- **Files**: All 5 XP services
- **Method**: `__init__()`
- **Common attributes**: `device_type`, `module_type_code`, `firmware_version`, `device_status`, `link_number`

#### 7. **Core Request Routing Structure** (85% identical)
- **Files**: All 5 XP services
- **Method**: `process_system_telegram(request: SystemTelegram)`
- **Common patterns**:
  - Device request validation via `_check_request_for_device()`
  - Discovery handling
  - RETURN_DATA function routing
  - WRITE_CONFIG function routing
  - Module type response generation

### Device-Specific Implementations That Should Remain

#### XP20 Specific
- `generate_humidity_response()` - DataPointType.HUMIDITY
- `generate_voltage_response()` - DataPointType.VOLTAGE

#### XP24 Specific  
- `generate_temperature_response()` - DataPointType.TEMPERATURE

#### XP33 Specific
- `generate_channel_states_response()` - DataPointType.CHANNEL_STATES
- `generate_channel_control_response()` - Individual channel control
- `set_channel_dimming()`, `activate_scene()` - Device-specific logic
- `get_technical_specs()` - Variant-specific specs

#### XP130 Specific
- `generate_ip_config_response()` - DataPointType.VOLTAGE
- `generate_temperature_response()` - Custom temperature simulation

#### XP230 Specific
- `generate_temperature_response()` - Custom temperature simulation

## Proposed Solution

### Phase 1: Base Response Generation Methods

Move the following methods to `BaseServerService`:

#### 1. Core Response Generators

```python
def generate_discovery_response(self) -> str:


    def generate_version_response(self, request: SystemTelegram) -> Optional[str]


    def generate_status_response(self, request: SystemTelegram,
                                 status_data_point: DataPointType = DataPointType.NONE) -> Optional[str]


    def generate_link_number_response(self, request: SystemTelegram) -> Optional[str]


    def set_link_number(self, request: SystemTelegram, new_link_number: int) -> Optional[str]
```

#### 2. Helper Methods
```python
def _build_response_telegram(self, data_part: str) -> str
def _log_response(self, response_type: str, telegram: str) -> None
```

### Phase 2: Enhanced Base Class Properties

Add common properties to `BaseServerService`:
```python
def __init__(self, serial_number: str):
    self.serial_number = serial_number
    self.logger = logging.getLogger(__name__)
    
    # Common device properties (must be set by subclasses)
    self.device_type: str = None
    self.module_type_code: int = None
    self.firmware_version: str = None
    self.device_status: str = "OK"
    self.link_number: int = 1
```

### Phase 3: Template Method Pattern for Request Processing

Implement a template method pattern for `process_system_telegram()`:

```python
def process_system_telegram(self, request: SystemTelegram) -> Optional[str]:
    """Template method for processing system telegrams"""
    if not self._check_request_for_device(request):
        return None

    if request.system_function == SystemFunction.DISCOVERY:
        return self.generate_discovery_response()

    elif request.system_function == SystemFunction.READ_DATAPOINT:
        return self._handle_return_data_request(request)

    elif request.system_function == SystemFunction.WRITE_CONFIG:
        return self._handle_write_config_request(request)

    self.logger.warning(f"Unhandled {self.device_type} request: {request}")
    return None


def _handle_return_data_request(self, request: SystemTelegram) -> Optional[str]:
    """Handle RETURN_DATA requests - can be overridden by subclasses"""
    if request.data_point_id == DataPointType.VERSION:
        return self.generate_version_response(request)
    elif request.data_point_id in [DataPointType.NONE, DataPointType.STATUS_QUERY]:
        return self.generate_status_response(request, request.data_point_id)
    elif request.data_point_id == DataPointType.LINK_NUMBER:
        return self.generate_link_number_response(request)
    elif request.data_point_id == DataPointType.MODULE_TYPE_CODE:
        return self.generate_module_type_response(request)

    # Allow device-specific handlers
    return self._handle_device_specific_data_request(request)


def _handle_device_specific_data_request(self, request: SystemTelegram) -> Optional[str]:
    """Override in subclasses for device-specific data requests"""
    return None


def _handle_write_config_request(self, request: SystemTelegram) -> Optional[str]:
    """Handle WRITE_CONFIG requests"""
    if request.data_point_id == DataPointType.LINK_NUMBER:
        return self.set_link_number(request, 1)  # Default implementation

    return self._handle_device_specific_config_request(request)


def _handle_device_specific_config_request(self, request: SystemTelegram) -> Optional[str]:
    """Override in subclasses for device-specific config requests"""
    return None
```

## Implementation Benefits

### Code Reduction
- **Estimated LOC reduction**: ~400+ lines across all services
- **Duplication elimination**: ~85% of common code consolidated

### Consistency Improvements
- Unified telegram formatting
- Consistent error handling and logging
- Standardized response generation patterns

### Maintainability Gains
- Single point of change for common functionality
- Easier testing of shared behaviors
- Reduced regression risk when modifying common features

### Future Extension Benefits
- New device types can inherit 80%+ of functionality
- Common enhancements benefit all devices automatically
- Clear separation between common and device-specific logic

## Migration Strategy

### Step 1: Extend BaseServerService
- Add common response generation methods
- Add helper methods for telegram construction
- Add template method for request processing

### Step 2: Update Individual Services
- Remove duplicated methods
- Override `_handle_device_specific_data_request()` where needed
- Update constructors to call base class properly
- Ensure all tests continue to pass

### Step 3: Verification
- Run comprehensive test suite
- Verify identical behavior for all existing functionality
- Performance testing to ensure no regression

## Risk Assessment

### Low Risk
- Discovery response generation (100% identical)
- Version response generation (single template parameter)
- Link number operations (100% identical)

### Medium Risk  
- Status response (minor DataPointType variation for XP33)
- Request processing template (need careful subclass method design)

### Mitigation Strategies
- Comprehensive unit tests for all moved functionality
- Integration tests to verify end-to-end behavior
- Gradual migration with service-by-service verification

## Success Criteria

1. **Code Duplication**: Reduce duplicated code by >80%
2. **Test Coverage**: Maintain 100% test coverage for all moved functionality
3. **Behavior Preservation**: Zero functional regressions
4. **Performance**: No measurable performance impact
5. **Maintainability**: Clear separation between base and device-specific logic

## Files Impacted

### Modified Files
- `src/xp/services/base_server_service.py` - Enhanced with common functionality
- `src/xp/services/xp24_server_service.py` - Remove duplicated code
- `src/xp/services/xp20_server_service.py` - Remove duplicated code  
- `src/xp/services/xp130_server_service.py` - Remove duplicated code
- `src/xp/services/xp230_server_service.py` - Remove duplicated code
- `src/xp/services/xp33_server_service.py` - Remove duplicated code

### Test Files
- Update all corresponding test files to verify base class functionality
- Add tests for new template method patterns
- Ensure device-specific behavior testing remains comprehensive