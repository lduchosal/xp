from enum import Enum
from typing import Optional


class SystemFunction(str, Enum):
    """System function codes for system telegrams"""

    DISCOVERY = "01"  # Discovery function
    READ_DATAPOINT = "02"  # Read datapoint
    READ_CONFIG = "03"  # Read configuration
    WRITE_CONFIG = "04"  # Write configuration
    BLINK = "05"  # Blink LED function
    UNBLINK = "06"  # Unblink LED function
    ACK = "18"  # Acknowledge response
    NAK = "19"  # Not acknowledge response
    ACTION = "27"  # Action function

    @classmethod
    def from_code(cls, code: str) -> Optional["SystemFunction"]:
        """Get SystemFunction from code string"""
        for func in cls:
            if func.value == code:
                return func
        return None
