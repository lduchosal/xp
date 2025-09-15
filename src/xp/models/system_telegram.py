"""System telegram model for console bus communication.

System telegrams are used for system-related information like updating firmware
and reading temperature from modules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

from .telegram import Telegram

class SystemFunction(Enum):
    """System function codes for system telegrams"""
    DISCOVERY = "01"  # Discovery function
    RETURN_DATA = "02"  # Return data function
    READ_CONFIG = "03"  # Read configuration
    WRITE_CONFIG = "04"  # Write configuration
    BLINK = "05"  # Blink LED function
    UNBLINK = "06"  # Unblink LED function
    ACK = "18"  # Acknowledge response
    NAK = "19"  # Not acknowledge response
    ACTION = "27"  # Action function

    @classmethod
    def from_code(cls, code: str) -> Optional['SystemFunction']:
        """Get SystemFunction from code string"""
        for func in cls:
            if func.value == code:
                return func
        return None


class DataPointType(Enum):
    """Data point types for system telegrams"""
    STATUS = "00"       # General status
    VERSION = "02"      # Version information
    LINK_NUMBER = "04"  # Link number data point
    MODULE_TYPE = "07"  # Module type data point
    STATUS_QUERY = "10" # Status query data point
    CHANNEL_STATES = "12" # Channel states (XP33)
    CHANNEL_1 = "13"    # Individual channel 1 control (XP33)
    CHANNEL_2 = "14"    # Individual channel 2 control (XP33)
    CHANNEL_3 = "15"    # Individual channel 3 control (XP33)
    CURRENT = "17"      # Current data point
    TEMPERATURE = "18"  # Temperature data point
    HUMIDITY = "19"     # Humidity data point
    VOLTAGE = "20"      # Voltage data point
    NETWORK_CONFIG = "20"  # Network configuration (alias for voltage in XP130)
    # Legacy alias

    @classmethod
    def from_code(cls, code: str) -> Optional['DataPointType']:
        """Get DataPointType from code string"""
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None


@dataclass
class SystemTelegram(Telegram):
    """
    Represents a parsed system telegram from the console bus.
    
    Format: <S{serial_number}F{function_code}D{data_point_id}{checksum}>
    Example: <S0020012521F02D18FN>
    """
    serial_number: str = ""
    system_function: Optional[SystemFunction] = None
    data_point_id: DataPointType = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def function_description(self) -> str:
        """Get human-readable function description"""
        descriptions = {
            SystemFunction.DISCOVERY: "Discovery",
            SystemFunction.RETURN_DATA: "Return Data",
            SystemFunction.READ_CONFIG: "Read Configuration",
            SystemFunction.WRITE_CONFIG: "Write Configuration",
            SystemFunction.BLINK: "Blink LED",
            SystemFunction.UNBLINK: "Unblink LED",
            SystemFunction.ACK: "Acknowledge",
            SystemFunction.NAK: "Not Acknowledge"
        }
        return descriptions.get(self.system_function, "Unknown Function")
    
    @property
    def data_point_description(self) -> str:
        """Get human-readable data point description"""
        descriptions = {
            DataPointType.STATUS: "Status",
            DataPointType.VERSION: "Version",
            DataPointType.LINK_NUMBER: "Link Number",
            DataPointType.MODULE_TYPE: "Module Type",
            DataPointType.STATUS_QUERY: "Status Query",
            DataPointType.CHANNEL_STATES: "Channel States",
            DataPointType.CHANNEL_1: "Channel 1 Control",
            DataPointType.CHANNEL_2: "Channel 2 Control", 
            DataPointType.CHANNEL_3: "Channel 3 Control",
            DataPointType.TEMPERATURE: "Temperature",
            DataPointType.HUMIDITY: "Humidity",
            DataPointType.VOLTAGE: "Voltage", 
            DataPointType.CURRENT: "Current",
        }
        return descriptions.get(self.data_point_id, "Unknown Data Point")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "system_function": {
                "code": self.system_function.value,
                "description": self.function_description
            },
            "data_point_id": {
                "code": self.data_point_id.value,
                "description": self.data_point_description
            },
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": "system"
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"System Telegram: {self.function_description} "
            f"for {self.data_point_description} "
            f"from device {self.serial_number}"
        )