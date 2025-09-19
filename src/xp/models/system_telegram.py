"""System telegram model for console bus communication.

System telegrams are used for system-related information like updating firmware
and reading temperature from modules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from .datapoint_type import DataPointType
from .system_function import SystemFunction
from .telegram import Telegram


@dataclass
class SystemTelegram(Telegram):
    """
    Represents a parsed system telegram from the console bus.

    Format: <S{serial_number}F{function_code}D{data_point_id}{checksum}>
    Examples: <S0020012521F02D18FN>
    """

    serial_number: str = ""
    system_function: Optional[SystemFunction] = None
    data_point_id: DataPointType = DataPointType.NONE

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def function_description(self) -> str:
        """Get human-readable function description"""
        descriptions = {
            SystemFunction.DISCOVERY: "Discovery",
            SystemFunction.READ_DATAPOINT: "Read Data point",
            SystemFunction.READ_CONFIG: "Read Configuration",
            SystemFunction.WRITE_CONFIG: "Write Configuration",
            SystemFunction.BLINK: "Blink LED",
            SystemFunction.UNBLINK: "Unblink LED",
            SystemFunction.ACK: "Acknowledge",
            SystemFunction.NAK: "Not Acknowledge",
        }
        return descriptions.get(self.system_function, "Unknown Function")

    @property
    def data_point_description(self) -> str:
        """Get human-readable data point description"""
        descriptions = {
            DataPointType.NONE: "None",
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "system_function": {
                "code": self.system_function.value,
                "description": self.function_description,
            },
            "data_point_id": {
                "code": self.data_point_id.value,
                "description": self.data_point_description,
            },
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": "system",
        }

    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"System Telegram: {self.function_description} "
            f"for {self.data_point_description} "
            f"from device {self.serial_number}"
        )
