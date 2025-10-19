"""Conbus connection status model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConbusConnectionStatus:
    """Represents the current connection status.

    Attributes:
        connected: Whether currently connected.
        ip: IP address of the connection.
        port: Port number of the connection.
        last_activity: Timestamp of last activity.
        error: Error message if connection failed.
    """

    connected: bool
    ip: str
    port: int
    last_activity: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the connection status.
        """
        return {
            "connected": self.connected,
            "ip": self.ip,
            "port": self.port,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "error": self.error,
        }
