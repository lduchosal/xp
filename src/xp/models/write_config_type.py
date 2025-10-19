"""Write config type enumeration."""

from enum import Enum
from typing import Optional


class WriteConfigType(str, Enum):
    """Write Config types for system telegrams.

    Attributes:
        LINK_NUMBER: Link number configuration (code 04).
        MODULE_NUMBER: Module number configuration (code 05).
        SYSTEM_TYPE: System type configuration (code 06).
    """

    LINK_NUMBER = "04"
    MODULE_NUMBER = "05"
    SYSTEM_TYPE = "06"  # 00 CP, 01 XP, 02 MIXED

    @classmethod
    def from_code(cls, code: str) -> Optional["WriteConfigType"]:
        """Get WriteConfigType from code string.

        Args:
            code: Configuration type code string.

        Returns:
            WriteConfigType instance if found, None otherwise.
        """
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None
