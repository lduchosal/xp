from enum import Enum
from typing import Optional

class DataPointType(str, Enum):
    """Data point types for system telegrams"""

    MODULE_TYPE = "00"  # General status
    HW_VERSION = "01"  # Hardware version information
    SW_VERSION = "02"  # Software version information
    SERIAL_NUMBER = "03"  # Serial number
    LINK_NUMBER = "04"  # Link number
    MODULE_NUMBER = "05"  # Module number
    SYSTEM_TYPE = "06"  # System type
    MODULE_TYPE_CODE = "07"  # Module type code
    MODULE_TYPE_ID = "08"  # Module type id
    MODULE_STATE = "09"  # Module state
    MODULE_ERROR_CODE = "10"  # Status query data point
    MODULE_INPUT_STATE = "11"  # Module input state
    MODULE_OUTPUT_STATE = "12"  # Channel states (XP33)
    MODULE_FW_CRC = "13"  # Module Firmware CRC
    MODULE_ACTION_TABLE_CRC = "14"  # Module Action Table CRC
    MODULE_LIGHT_LEVEL = "15"  # Module Light Level
    MODULE_OPERATING_HOURS = "16"  # Module Operating Hours
    MODULE_ENERGY_LEVEL = "17"  # Current data point
    TEMPERATURE = "18"  # Temperature data point
    SW_TOP_VERSION = "19"  # Software Top Version
    VOLTAGE = "20"  # VOLTAGE data point
    AUTO_REPORT_STATUS = "21"  # Auto Report Status

    @classmethod
    def from_code(cls, code: str) -> Optional["DataPointType"]:
        """Get DataPointType from code string"""
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None

