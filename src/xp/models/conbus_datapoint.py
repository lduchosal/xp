from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from .datapoint_type import DataPointType
from .reply_telegram import ReplyTelegram
from .system_function import SystemFunction


@dataclass
class ConbusDatapointResponse:
    """Represents a response from Conbus send operation"""

    success: bool
    serial_number : Optional[str] = None,
    system_function : Optional[SystemFunction] = None,
    datapoint_type : Optional[DataPointType] = None,
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
            "serial_number": self.serial_number,
            "system_function": self.system_function,
            "datapoint_type": self.datapoint_type,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
