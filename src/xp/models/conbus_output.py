from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from .action_type import ActionType
from .output_telegram import OutputTelegram
from .reply_telegram import ReplyTelegram


@dataclass
class ConbusOutputResponse:
    """Represents a response from Conbus send operation"""

    success: bool
    serial_number: str
    output_number: int
    action_type: ActionType
    timestamp: datetime
    output_telegram: Optional[OutputTelegram] = None
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list[str]] = None
    datapoint_telegram: Optional[ReplyTelegram] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
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
