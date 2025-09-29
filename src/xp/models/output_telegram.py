"""XP output telegram model for console bus communication.

XP output telegrams are used for controlling relay inputs on XP modules.
Each XP24 module has 4 inputs (0-3) that can be pressed or released.
Each XP33 module has 3 inputs (0-2) that can be pressed or released.
Each XP31 module has 1 inputs (0-0) that can be pressed or released.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .action_type import ActionType
from .system_function import SystemFunction
from .telegram import Telegram


@dataclass
class OutputTelegram(Telegram):
    """
    Represents a parsed XP output telegram from the console bus.

    Format: <S{serial_number}F27D{input:02d}{action}{checksum}>
    Examples: <S0012345008F27D00AAFN>
    """

    serial_number: str = ""
    output_number: Optional[int] = (
        None  # 0-3 for XP24 modules, 0-2 for XP33, 0 for XP31
    )
    action_type: Optional[ActionType] = None
    system_function: SystemFunction = SystemFunction.ACTION

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def action_description(self) -> str:
        """Get human-readable action description"""
        descriptions = {
            ActionType.OFF_PRESS: "Press (Make)",
            ActionType.ON_RELEASE: "Release (Break)",
        }
        return (
            descriptions.get(self.action_type, "Unknown Action")
            if self.action_type
            else "Unknown Action"
        )

    @property
    def input_description(self) -> str:
        """Get human-readable input description"""
        return f"Input {self.output_number}"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "system_function": self.system_function,
            "output_number": self.output_number,
            "input_description": self.input_description,
            "action_type": {
                "code": self.action_type.value if self.action_type else None,
                "description": self.action_description,
            },
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"XP Output: {self.action_description} "
            f"on {self.input_description} "
            f"for device {self.serial_number}"
        )
