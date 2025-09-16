from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class ConbusConnectionStatus:
    """Represents the current connection status"""

    connected: bool
    ip: str
    port: int
    last_activity: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "connected": self.connected,
            "ip": self.ip,
            "port": self.port,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "error": self.error,
        }
