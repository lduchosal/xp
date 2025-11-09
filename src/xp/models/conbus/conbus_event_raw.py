"""Conbus event raw response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConbusEventRawResponse:
    """Represents a response from Conbus event raw operation.

    Attributes:
        success: Whether the operation was successful.
        sent_telegrams: List of event telegrams sent (MAKE and BREAK).
        received_telegrams: List of all telegrams received.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.
    """

    success: bool
    sent_telegrams: Optional[list[str]] = None
    received_telegrams: Optional[list[str]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamp and telegram lists if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.sent_telegrams is None:
            self.sent_telegrams = []
        if self.received_telegrams is None:
            self.received_telegrams = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response.
        """
        return {
            "success": self.success,
            "sent_telegrams": self.sent_telegrams,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
