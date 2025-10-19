"""Action type enumeration for XP24 telegrams."""

from enum import Enum
from typing import Optional


class ActionType(Enum):
    """Action types for XP24 telegrams.

    Attributes:
        OFF_PRESS: Make action (activate relay).
        ON_RELEASE: Break action (deactivate relay).
    """

    OFF_PRESS = "AA"  # Make action (activate relay)
    ON_RELEASE = "AB"  # Break action (deactivate relay)

    @classmethod
    def from_code(cls, code: str) -> Optional["ActionType"]:
        """Get ActionType from code string.

        Args:
            code: Action code string.

        Returns:
            ActionType instance if found, None otherwise.
        """
        for action in cls:
            if action.value == code:
                return action
        return None
