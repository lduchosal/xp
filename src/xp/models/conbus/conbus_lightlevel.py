# Copyright (c) 2025 ldvchosal
"""Conbus light level response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


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
    level: int | None
    timestamp: datetime
    sent_telegram: str | None = None
    received_telegrams: list[str] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        """Initialize received_telegrams if not provided."""
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
            "output_number": self.output_number,
            "level": self.level,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
