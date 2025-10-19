"""Conbus blink response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from xp.models import ConbusResponse
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram


@dataclass
class ConbusBlinkResponse:
    """Represents a response from Conbus send operation.

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        operation: Operation type (get or set).
        system_function: System function used.
        response: Response from Conbus operation.
        reply_telegram: Reply telegram received.
        sent_telegram: System telegram sent.
        received_telegrams: List of telegrams received.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.
    """

    success: bool
    serial_number: str
    operation: str
    system_function: SystemFunction
    response: Optional[ConbusResponse] = None
    reply_telegram: Optional[ReplyTelegram] = None
    sent_telegram: Optional[SystemTelegram] = None
    received_telegrams: Optional[list] = None
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
        result = {
            "success": self.success,
            "serial_number": self.serial_number,
            "operation": self.operation,
            "system_function": (
                self.system_function.name if self.system_function else None
            ),
            "sent_telegram": (
                self.sent_telegram.to_dict()
                if self.sent_telegram and hasattr(self.sent_telegram, "to_dict")
                else str(self.sent_telegram) if self.sent_telegram else None
            ),
            "reply_telegram": (
                self.reply_telegram.to_dict()
                if self.reply_telegram and hasattr(self.reply_telegram, "to_dict")
                else str(self.reply_telegram) if self.reply_telegram else None
            ),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

        # Only include these if they have values
        if self.received_telegrams:
            result["received_telegrams"] = self.received_telegrams
        if self.error:
            result["error"] = self.error

        return result
