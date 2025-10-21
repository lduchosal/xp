"""System telegram model for console bus communication.

System telegrams are used for system-related information like updating firmware
and reading temperature from modules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram import Telegram
from xp.models.telegram.telegram_type import TelegramType


@dataclass
class SystemTelegram(Telegram):
    """Represents a parsed system telegram from the console bus.

    Format: <S{serial_number}F{function_code}D{datapoint_type}{checksum}>
    Examples: <S0020012521F02D18FN>

    Attributes:
        serial_number: Serial number of the device (0020012521)
        system_function: System function code (02).
        data: Data payload (18)
        datapoint_type: Type of datapoint (18).
    """

    serial_number: str = ""
    system_function: Optional[SystemFunction] = None
    data: str = ""
    datapoint_type: Optional[DataPointType] = None

    def __post_init__(self) -> None:
        """Initialize timestamp and telegram type."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.telegram_type = TelegramType.SYSTEM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the system telegram.
        """
        return {
            "serial_number": self.serial_number,
            "system_function": (
                {
                    "code": (
                        self.system_function.value if self.system_function else None
                    ),
                    "description": (
                        self.system_function.name if self.system_function else None
                    ),
                }
                if self.system_function
                else None
            ),
            "datapoint_type": (
                {
                    "code": self.datapoint_type.value if self.datapoint_type else None,
                    "description": (
                        self.datapoint_type.name if self.datapoint_type else None
                    ),
                }
                if self.datapoint_type
                else None
            ),
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": self.telegram_type.value,
        }

    def __str__(self) -> str:
        """Human-readable string representation.

        Returns:
            Formatted string representation.
        """
        system_func_name = (
            self.system_function.name if self.system_function else "Unknown"
        )
        data = self.data or "None"
        data = self.datapoint_type.name if self.datapoint_type else data
        return (
            f"System Telegram: {system_func_name} "
            f"with data {data} "
            f"from device {self.serial_number}"
        )
