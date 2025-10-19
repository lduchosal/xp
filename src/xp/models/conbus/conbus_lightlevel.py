"""Conbus light level response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConbusLightlevelResponse:
    """Represents a response from Conbus lightlevel operation.

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        output_number: Output number queried.
        level: Light level value (0-100).
        timestamp: Timestamp of the response.
        sent_telegram: Telegram sent to device.
        received_telegrams: List of telegrams received.
        error: Error message if operation failed.
    """

    success: bool
    serial_number: str
    output_number: int
    level: Optional[int]
    timestamp: datetime
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list[str]] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize received_telegrams if not provided."""
        if self.received_telegrams is None:
            self.received_telegrams = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response.
        """
        return {
            "success": self.success,
            "serial_number": self.serial_number,
            "output_number": self.output_number,
            "level": self.level,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
