"""Conbus custom response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from xp.models.telegram.reply_telegram import ReplyTelegram


@dataclass
class ConbusCustomResponse:
    """Represents a response from Conbus send operation.

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        function_code: Function code used.
        data: Data payload.
        sent_telegram: Telegram sent to device.
        received_telegrams: List of telegrams received.
        reply_telegram: Parsed reply telegram.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.
    """

    success: bool
    serial_number: Optional[str] = None
    function_code: Optional[str] = None
    data: Optional[str] = None
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list] = None
    reply_telegram: Optional[ReplyTelegram] = None
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
            "serial_number": self.serial_number,
            "function_code": self.function_code,
            "data": self.data,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
