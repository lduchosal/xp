from enum import Enum
from typing import Optional

class WriteConfigType(str, Enum):
    """Write Config types for system telegrams"""

    LINK_NUMBER = "04"
    MODULE_NUMBER = "05"
    XP_FLAG_TELEGRAM = "06"

    @classmethod
    def from_code(cls, code: str) -> Optional["WriteConfigType"]:
        """Get DataPointType from code string"""
        for dp_type in cls:
            if dp_type.value == code:
                return dp_type
        return None

