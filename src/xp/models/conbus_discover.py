from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class ConbusDiscoverResponse:
    """Represents a response from Conbus send operation"""

    success: bool
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list] = None
    discovered_devices: Optional[list] = None
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
            "discovered_devices": self.discovered_devices,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
