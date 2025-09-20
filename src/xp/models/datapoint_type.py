from enum import Enum
from typing import Optional


class DataPointType(str, Enum):
    """Data point types for system telegrams"""

    NONE = "00"  # General status
    VERSION = "02"  # Version information
    UNKNOWN_03 = "03"  #
    LINK_NUMBER = "04"  # Link number data point
    UNKNOWN_05 = "05"  #
    UNKNOWN_06 = "06"  #
    MODULE_TYPE = "07"  # Module type data point
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

class DatapointTypeName(str, Enum):
    """Supported telegram types for Conbus client send operations"""

    UNKNOWN = "unknown"
    VERSION = "version"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    HUMIDITY = "humidity"
    LINK_NUMBER = "link_number"
    CHANNEL_STATES = "channelstates"
