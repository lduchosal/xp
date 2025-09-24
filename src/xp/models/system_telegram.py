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

    Format: <S{serial_number}F{function_code}D{datapoint_type}{checksum}>
    Examples: <S0020012521F02D18FN>
    """

    serial_number: str = ""
    system_function: Optional[SystemFunction] = None
    data: str = ""
    datapoint_type: Optional[DataPointType] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "system_function": {
                "code": self.system_function.value if self.system_function else None,
                "description": self.system_function.name if self.system_function else None,
            } if self.system_function else None,
            "datapoint_type": {
                "code": self.datapoint_type.value if self.datapoint_type else None,
                "description": self.datapoint_type.name if self.datapoint_type else None,
            } if self.datapoint_type else None,
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": "system",
        }

    def __str__(self) -> str:
        """Human-readable string representation"""
        system_func_name = self.system_function.name if self.system_function else "Unknown"
        datapoint_name = self.datapoint_type.name if self.datapoint_type else "Unknown"
        return (
            f"System Telegram: {system_func_name} "
            f"for {datapoint_name} "
            f"from device {self.serial_number}"
        )
