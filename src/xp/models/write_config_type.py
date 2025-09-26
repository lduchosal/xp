from enum import Enum
from typing import Optional


class WriteConfigType(str, Enum):
    """Write Config types for system telegrams"""

    LINK_NUMBER = "04"
    MODULE_NUMBER = "05"
    SYSTEM_TYPE = "06"  # 00 CP, 01 XP, 02 MIXED

    @classmethod
    def from_code(cls, code: str) -> Optional["WriteConfigType"]:
        """Get DataPointType from code string"""
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None
