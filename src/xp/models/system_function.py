from enum import Enum
from typing import Optional


class SystemFunction(str, Enum):
    """System function codes for system telegrams"""

    DISCOVERY = "01"  # Discover function
    READ_DATAPOINT = "02"  # Read datapoint
    READ_CONFIG = "03"  # Read configuration
    WRITE_CONFIG = "04"  # Write configuration
    BLINK = "05"  # Blink LED function
    UNBLINK = "06"  # Unblink LED function
    ACK = "18"  # Acknowledge response
    NAK = "19"  # Not acknowledge response
    ACTION = "27"  # Action function

    def get_description(self) -> str:
        """Get the description of the SystemFunction"""
        descriptions = {
            self.DISCOVERY: "Discover function",
            self.READ_DATAPOINT: "Read datapoint",
            self.READ_CONFIG: "Read configuration",
            self.WRITE_CONFIG: "Write configuration",
            self.BLINK: "Blink LED function",
            self.UNBLINK: "Unblink LED function",
            self.ACK: "Acknowledge response",
            self.NAK: "Not acknowledge response",
            self.ACTION: "Action function",
        }
        return descriptions.get(self, "Unknown function")

    @classmethod
    def from_code(cls, code: str) -> Optional["SystemFunction"]:
        """Get SystemFunction from code string"""
        for func in cls:
            if func.value == code:
                return func
        return None
