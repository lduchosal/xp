"""Conbus output response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from xp.models.telegram.action_type import ActionType
from xp.models.telegram.output_telegram import OutputTelegram
from xp.models.telegram.reply_telegram import ReplyTelegram


@dataclass
class ConbusOutputResponse:
    """Represents a response from Conbus send operation.

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        output_number: Output number controlled.
        action_type: Type of action performed.
        timestamp: Timestamp of the response.
        output_telegram: Output telegram sent.
        sent_telegram: Raw telegram sent to device.
        received_telegrams: List of telegrams received.
        datapoint_telegram: Datapoint telegram received.
        error: Error message if operation failed.
    """

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
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
