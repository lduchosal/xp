from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from xp.models import TelegramType


@dataclass
class ConbusSendRequest:
    """Represents a Conbus send request"""

    telegram_type: TelegramType
    target_serial: Optional[str] = None
    function_code: Optional[str] = None
    data_point_code: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "telegram_type": self.telegram_type.value,
            "target_serial": self.target_serial,
            "function_code": self.function_code,
            "data_point_code": self.data_point_code,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
