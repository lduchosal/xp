"""Conbus discover response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConbusDiscoverResponse:
    """Represents a response from Conbus send operation.

    Attributes:
        success: Whether the operation was successful.
        sent_telegram: Telegram sent to discover devices.
        received_telegrams: List of telegrams received.
        discovered_devices: List of discovered device serial numbers.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.
    """

    success: bool
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list[str]] = None
    discovered_devices: Optional[list[str]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamp and received_telegrams if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.received_telegrams is None:
            self.received_telegrams = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response.
        """
        return {
            "success": self.success,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "discovered_devices": self.discovered_devices,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
