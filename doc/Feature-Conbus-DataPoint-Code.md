# Conbus DataPoint Code Specification

This document specifies the missing datapoints in the F02 (Read Data point) function for Conbus communication protocol and their implementation requirements.

## Overview

The Conbus protocol uses Function 02 (F02) for returning data from various datapoints. Based on analysis of the captured test data and current implementation, the following datapoints need to be implemented or documented.

## Currently Implemented Datapoints

The following datapoints are already implemented in the codebase:

- **00**: Status - General device status (`DataPointType.STATUS`)
- **02**: Version - Firmware version information (`DataPointType.VERSION`)
- **04**: LINK_NUMBER - Device link configuration (`DataPointType.LINK_NUMBER`)
- **17**: Current - Current measurement data (`DataPointType.CURRENT`)
- **18**: Temperature - Temperature sensor data (`DataPointType.TEMPERATURE`)
- **19**: Humidity - Humidity sensor data (`DataPointType.HUMIDITY`)
- **20**: VOLTAGE - VOLTAGE measurement data (`DataPointType.VOLTAGE`)

## Missing Datapoints Requiring Implementation

Based on the test data analysis, the following datapoints are missing from the current implementation:

### Datapoint 01 - Device Type Identifier
**Purpose**: Returns the device type identifier for the module
- **Request**: `<S{serial}F02D01{checksum}>`
- **Response**: `<R{serial}F02D01{device_type}{checksum}>`
- **Example**: `<R0020044989F02D01XP24FH>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `DEVICE_TYPE = "01"`

### Datapoint 03 - Serial Number
**Purpose**: Returns the device serial number
- **Request**: `<S{serial}F02D03{checksum}>`
- **Response**: `<R{serial}F02D03{serial_number}{checksum}>`
- **Example**: `<R0020044989F02D030020044989FB>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `SERIAL_NUMBER = "03"`

### Datapoint 05 - Error Status
**Purpose**: Returns error status information from the device
- **Request**: `<S{serial}F02D05{checksum}>`
- **Response**: `<R{serial}F02D05{error_code}{checksum}>`
- **Example**: `<R0020044989F02D050008FF>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `ERROR_STATUS = "05"`

### Datapoint 06 - Operating Mode
**Purpose**: Returns current operating mode configuration
- **Request**: `<S{serial}F02D06{checksum}>`
- **Response**: `<R{serial}F02D06{mode}{checksum}>`
- **Example**: `<R0020044989F02D0600FO>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `OPERATING_MODE = "06"`

### Datapoint 07 - Measurement Mode
**Purpose**: Returns measurement mode settings
- **Request**: `<S{serial}F02D07{checksum}>`
- **Response**: `<R{serial}F02D07{mode_config}{checksum}>`
- **Example**: `<R0020044989F02D0707FI>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `MEASUREMENT_MODE = "07"`

### Datapoint 08 - Module Information
**Purpose**: Returns module-specific information
- **Request**: `<S{serial}F02D08{checksum}>`
- **Response**: `<R{serial}F02D08{module_info}{checksum}>`
- **Example**: `<R0020044989F02D08MIFE>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `MODULE_INFO = "08"`

### Datapoint 09 - Offset Calibration Data
**Purpose**: Returns offset calibration values
- **Request**: `<S{serial}F02D09{checksum}>`
- **Response**: `<R{serial}F02D09{offset_data}{checksum}>`
- **Example**: `<R0020044989F02D09OFFBO>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `OFFSET_DATA = "09"`

### Datapoint 10 - Range Configuration
**Purpose**: Returns measurement range configuration
- **Request**: `<S{serial}F02D10{checksum}>`
- **Response**: `<R{serial}F02D10{range_config}{checksum}>`
- **Example**: `<R0020044989F02D1000FJ>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `RANGE_DATA = "10"`

### Datapoint 11 - Reserved Data (Type 1)
**Purpose**: Reserved datapoint for future use
- **Request**: `<S{serial}F02D11{checksum}>`
- **Response**: `<R{serial}F02D11{reserved_data}{checksum}>`
- **Example**: `<R0020044989F02D11xxxx0000FI>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `RESERVED_11 = "11"`

### Datapoint 12 - Reserved Data (Type 2)
**Purpose**: Reserved datapoint for future use
- **Request**: `<S{serial}F02D12{checksum}>`
- **Response**: `<R{serial}F02D12{reserved_data}{checksum}>`
- **Example**: `<R0020044989F02D12xxxx0000FL>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `RESERVED_12 = "12"`

### Datapoint 13 - Module Type Information
**Purpose**: Returns detailed module type and capabilities
- **Request**: `<S{serial}F02D13{checksum}>`
- **Response**: `<R{serial}F02D13{module_type_info}{checksum}>`
- **Example**: `<R0020044989F02D13EIDCDONMFJ>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `MODULE_TYPE = "13"`

### Datapoint 14 - Module Name
**Purpose**: Returns human-readable module name
- **Request**: `<S{serial}F02D14{checksum}>`
- **Response**: `<R{serial}F02D14{module_name}{checksum}>`
- **Example**: `<R0020044989F02D14MFAELCIIFN>`
- **Implementation Location**: `src/xp/models/system_telegram.py` - Add `MODULE_NAME = "14"`

### Datapoint 15 - Measurement Data Format
**Purpose**: Returns measurement data in formatted output with units
- **Request**: `<S{serial}F02D15{checksum}>`
- **Response**: `<R{serial}F02D15{formatted_data}{checksum}>`
- **Example**: `<R0020044989F02D1500:000[%],01:000[%],02:000[%],03:000[%]HA>`
- **Data Format**: Channel-based data with units in brackets

### Datapoint 16 - Operating Hours Counter
**Purpose**: Returns operating hours in formatted output
- **Request**: `<S{serial}F02D16{checksum}>`
- **Response**: `<R{serial}F02D16{hours_data}{checksum}>`
- **Example**: `<R0020044989F02D1600:000[H],01:000[H],02:000[H],03:000[H]HD>`
- **Data Format**: Multi-channel hour counters with [H] unit indicator

### Datapoint 17 - Counter Data
**Purpose**: Returns counter data in numeric array format
- **Request**: `<S{serial}F02D17{checksum}>`
- **Response**: `<R{serial}F02D17{counter_data}{checksum}>`
- **Example**: `<R0020044989F02D1700:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]HC>`
- **Data Format**: Multi-channel counters with [NA] indicating not available

## Implementation Requirements

### 1. Update DataPointType Enum
Location: `src/xp/models/system_telegram.py:34-42`

Add the missing datapoint types to the `DataPointType` enum:

```python
class DataPointType(Enum):
    """Data point types for system telegrams"""
    STATUS = "00"           # General status (implemented)
    DEVICE_TYPE = "01"      # Device type identifier
    VERSION = "02"          # Firmware version (implemented)
    SERIAL_NUMBER = "03"    # Device serial number
    LINK_NUMBER = "04"      # Link number configuration (implemented)
    ERROR_STATUS = "05"     # Error status information
    OPERATING_MODE = "06"   # Operating mode configuration
    MEASUREMENT_MODE = "07" # Measurement mode setting
    MODULE_INFO = "08"      # Module information
    OFFSET_DATA = "09"      # Offset calibration data
    RANGE_DATA = "10"       # Range configuration data
    RESERVED_11 = "11"      # Reserved data point
    RESERVED_12 = "12"      # Reserved data point
    MODULE_TYPE = "13"      # Module type information
    MODULE_NAME = "14"      # Module name string
    MEASUREMENT_DATA = "15" # Measurement data format
    OPERATING_HOURS = "16"  # Operating hours counter
    CURRENT = "17"          # Current data point (implemented)
    TEMPERATURE = "18"      # Temperature data point (implemented)
    HUMIDITY = "19"         # Humidity data point (implemented)
    VOLTAGE = "20"          # VOLTAGE data point (implemented)
```

### 2. Update Response Generation Services
Location: `src/xp/services/xp24_server_service.py` and `src/xp/services/xp20_server_service.py`

Add response methods for each new datapoint in both XP24 and XP20 server services following the existing pattern:

```python
def generate_device_type_response(self, request: SystemTelegram) -> Optional[str]:
    """Generate device type response telegram"""
    if (request.system_function == SystemFunction.READ_DATAPOINT and
            request.datapoint_type == DataPointType.DEVICE_TYPE):
        data_part = f"R{self.serial_number}F02D01{self.device_type}"
        checksum = calculate_checksum(data_part)
        telegram = f"<{data_part}{checksum}>"
        return telegram
    return None
```

### 3. Update Description Mappings
Location: `src/xp/models/system_telegram.py:86-95`

Add descriptions for the new datapoints in the `data_point_description` property.

### 4. Update Process Methods
Update the `process_system_telegram` methods in both server services to handle the new datapoints.

## Test Data Reference

The implementation should handle the following test cases based on captured data:

```
Serial: 0020044989, Function: 02 (Read Data point)

D01 → XP24           (Device Type)
D03 → 0020044989     (Serial Number)
D05 → 0008           (Error Status)
D06 → 00             (Operating Mode)
D07 → 07             (Measurement Mode)
D08 → MI             (Module Info)
D09 → OFF            (Offset Data)
D10 → 00             (Range Data)
D11 → xxxx0000       (Reserved)
D12 → xxxx0000       (Reserved)
D13 → EIDCDONM       (Module Type)
D14 → MFAELCII       (Module Name)
D15 → 00:000[%],01:000[%],02:000[%],03:000[%]  (Measurement Data)
D16 → 00:000[H],01:000[H],02:000[H],03:000[H]  (Operating Hours)
D17 → 00:00000[NA],01:00000[NA],02:00000[NA],03:00000[NA]  (Counter Data)
```

## Priority Implementation Order

1. **High Priority**: Datapoints 01, 03, 05 (Device identification and error status)
2. **Medium Priority**: Datapoints 06, 07, 08 (Configuration and module info)
3. **Low Priority**: Datapoints 09-17 (Advanced features and reserved data)

This specification provides the complete roadmap for implementing the missing F02 datapoints in the Conbus protocol implementation.