from enum import Enum
from typing import Optional


class DataPointType(Enum):
    """Data point types for system telegrams"""

    NONE = "00"  # General status
    VERSION = "02"  # Version information
    LINK_NUMBER = "04"  # Link number data point
    MODULE_TYPE = "07"  # Module type data point
    STATUS_QUERY = "10"  # Status query data point
    CHANNEL_STATES = "12"  # Channel states (XP33)
    CHANNEL_1 = "13"  # Individual channel 1 control (XP33)
    CHANNEL_2 = "14"  # Individual channel 2 control (XP33)
    CHANNEL_3 = "15"  # Individual channel 3 control (XP33)
    CHANNEL_4 = "16"  # Individual channel 3 control (XP33)
    CURRENT = "17"  # Current data point
    TEMPERATURE = "18"  # Temperature data point
    HUMIDITY = "19"  # Humidity data point
    VOLTAGE = "20"  # Voltage data point
    NETWORK_CONFIG = "20"  # Network configuration (alias for voltage in XP130)
    # Legacy alias

    @classmethod
    def from_code(cls, code: str) -> Optional["DataPointType"]:
        """Get DataPointType from code string"""
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None


class DatapointTypeName(Enum):
    """Supported telegram types for Conbus client send operations"""

    UNKNOWN = "unknown"
    VERSION = "version"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    HUMIDITY = "humidity"
    LINK_NUMBER = "linknumber"
    CHANNEL_STATES = "channelstates"
