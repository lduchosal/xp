from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from . import ConbusResponse
from .reply_telegram import ReplyTelegram
from .system_function import SystemFunction
from .system_telegram import SystemTelegram


@dataclass
class ConbusBlinkResponse:
    """Represents a response from Conbus send operation"""

    success: bool
    serial_number: str
    operation: str
    system_function: SystemFunction
    response: Optional[ConbusResponse] = None
    reply_telegram: Optional[ReplyTelegram] = None
    sent_telegram: Optional[SystemTelegram] = None
    received_telegrams: Optional[list] = None
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
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
