# Copyright (c) 2025 ldvchosal
"""Conbus custom response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.utils.time_utils import local_now


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
    serial_number: str | None = None
    function_code: str | None = None
    data: str | None = None
    sent_telegram: str | None = None
    received_telegrams: list | None = None
    reply_telegram: ReplyTelegram | None = None
    error: str | None = None
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamp and received_telegrams if not provided."""
        if self.timestamp is None:
            self.timestamp = local_now()
        if self.received_telegrams is None:
            self.received_telegrams = []

    def to_dict(self) -> dict[str, Any]:
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
