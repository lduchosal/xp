from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConbusRequest:
    """Represents a Conbus send request"""

    serial_number: Optional[str] = None
    function_code: Optional[str] = None
    data: Optional[str] = None
    telegram: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "function_code": self.function_code,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class ConbusResponse:
    """Represents a response from Conbus send operation"""

    success: bool
    sent_telegrams: list[str]
    received_telegrams: list[str]
    timestamp: datetime
    error: str = ""
    serial_number: str = ""
    function_code: str = ""

    def __post_init__(self) -> None:
        self.timestamp = datetime.now()
        self.sent_telegrams = []
        self.received_telegrams = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "serial_number": self.serial_number,
            "function_code": self.function_code,
            "sent_telegrams": self.sent_telegrams,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
