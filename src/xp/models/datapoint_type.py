from enum import Enum
from typing import Optional

class DataPointType(str, Enum):
    """Data point types for system telegrams"""

    NONE = "00"  # General status
    VERSION = "02"  # Version information
    SERIAL_NUMBER = "03"  # Serial number
    LINK_NUMBER = "04"  # Link number data point
    UNKNOWN_05 = "05"  #
    UNKNOWN_06 = "06"  #
    MODULE_TYPE_CODE = "07"  # Module type data point
    UNKNOWN_08 = "08"  #
    UNKNOWN_09 = "09"  #
    STATUS_QUERY = "10"  # Status query data point
    UNKNOWN_11 = "11"  #
    CHANNEL_STATES = "12"  # Channel states (XP33)
    CHANNEL_1 = "13"  # Individual channel 1 control (XP33)
    CHANNEL_2 = "14"  # Individual channel 2 control (XP33)
    CHANNEL_3 = "15"  # Individual channel 3 control (XP33)
    CHANNEL_4 = "16"  # Individual channel 3 control (XP33)
    CURRENT = "17"  # Current data point
    TEMPERATURE = "18"  # Temperature data point
    HUMIDITY = "19"  # Humidity data point
    VOLTAGE = "20"  # Voltage data point

    @classmethod
    def from_code(cls, code: str) -> Optional["DataPointType"]:
        """Get DataPointType from code string"""
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None

    ModuleType"F02D00"
    HWVersion"F02D01"
    SWVersion"F02D02"
    SWTopVersion"F02D19"
    LinkNummer"F02D04"
    ModuleNummer"F02D05"
    SystemType"F02D06"
    ModuleTypeCode"F02D07"
    ModuleTypeId"F02D08"
    ModuleState"F02D09"
    ModuleErrorCode"F02D10"
    ModuleInputState"F02D11"
    ModuleOutputState"F02D12"
    ModuleFirmwareCRC"F02D13"
    ModuleActionTableCRC"F02D14"
    ModuleLightLevel"F02D15"
    ModuleOperatingHours"F02D16"
    ModuleEnergyLevel"F02D17"
    AutoReportStatus"F02D21"
    ModuleNumber"F02D05"