from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from .action_type import ActionType
from .input_telegram import InputTelegram
from .reply_telegram import ReplyTelegram


@dataclass
class ConbusInputResponse:
    """Represents a response from Conbus send operation"""

    success: bool
    serial_number: str
    input_number: int
    action_type: ActionType
    timestamp: datetime
    input_telegram: Optional[InputTelegram] = None
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list] = None
    datapoint_telegram: Optional[ReplyTelegram] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
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
