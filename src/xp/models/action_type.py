from enum import Enum
from typing import Optional


class ActionType(Enum):
    """Action types for XP24 telegrams"""

    RELEASE = "AA"  # Break action (deactivate relay)
    PRESS = "AB"  # Make action (activate relay)

    @classmethod
    def from_code(cls, code: str) -> Optional["ActionType"]:
        """Get ActionType from code string"""
        for action in cls:
            if action.value == code:
                return action
        return None
