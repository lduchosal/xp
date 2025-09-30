from enum import Enum
from typing import Optional


class ActionType(Enum):
    """Action types for XP24 telegrams"""

    OFF_PRESS = "AA"  # Make action (activate relay)
    ON_RELEASE = "AB"  # Break action (deactivate relay)

    @classmethod
    def from_code(cls, code: str) -> Optional["ActionType"]:
        """Get ActionType from code string"""
        for action in cls:
            if action.value == code:
                return action
        return None
