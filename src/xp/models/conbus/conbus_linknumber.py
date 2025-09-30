from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class ConbusLinknumberResponse:
    """Represents a response from Conbus link number operations (set/get)"""

    success: bool
    result: str
    serial_number: str
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list] = None
    link_number: Optional[int] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.received_telegrams is None:
            self.received_telegrams = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "result": self.result,
            "link_number": self.link_number,
            "serial_number": self.serial_number,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
