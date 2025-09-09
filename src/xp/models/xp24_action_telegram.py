"""XP24 action telegram model for console bus communication.

XP24 action telegrams are used for controlling relay inputs on XP24 modules.
Each XP24 module has 4 inputs (0-3) that can be pressed or released.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

from .telegram import Telegram


class ActionType(Enum):
    """Action types for XP24 telegrams"""
    PRESS = "AA"    # Make action (activate relay)
    RELEASE = "AB"  # Break action (deactivate relay)
    
    @classmethod
    def from_code(cls, code: str) -> Optional['ActionType']:
        """Get ActionType from code string"""
        for action in cls:
            if action.value == code:
                return action
        return None


@dataclass
class XP24ActionTelegram(Telegram):
    """
    Represents a parsed XP24 action telegram from the console bus.
    
    Format: <S{serial_number}F27D{input:02d}{action}{checksum}>
    Example: <S0020044964F27D00AAFN>
    """
    serial_number: str = ""
    input_number: int = 0  # 0-3 for XP24 modules
    action_type: Optional[ActionType] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def action_description(self) -> str:
        """Get human-readable action description"""
        descriptions = {
            ActionType.PRESS: "Press (Make)",
            ActionType.RELEASE: "Release (Break)"
        }
        return descriptions.get(self.action_type, "Unknown Action")
    
    @property
    def input_description(self) -> str:
        """Get human-readable input description"""
        return f"Input {self.input_number}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "input_number": self.input_number,
            "input_description": self.input_description,
            "action_type": {
                "code": self.action_type.value if self.action_type else None,
                "description": self.action_description
            },
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": "xp24_action"
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"XP24 Action: {self.action_description} "
            f"on {self.input_description} "
            f"for device {self.serial_number}"
        )