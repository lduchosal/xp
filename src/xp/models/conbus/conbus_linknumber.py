# Copyright (c) 2025 ldvchosal
"""Conbus link number response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from xp.utils.time_utils import local_now


@dataclass
class ConbusLinknumberResponse:
    """Represents a response from Conbus link number operations (set/get).

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        result: Result message from operation.
        sent_telegram: Telegram sent to device.
        received_telegrams: List of telegrams received.
        link_number: Link number value.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.

    """

    success: bool
    serial_number: str
    result: str
    sent_telegram: str | None = None
    received_telegrams: list | None = None
    link_number: int | None = None
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
            "result": self.result,
            "link_number": self.link_number,
            "serial_number": self.serial_number,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
