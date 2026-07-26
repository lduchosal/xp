# Copyright (c) 2025 ldvchosal
"""Conbus raw response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from xp.utils.time_utils import local_now


@dataclass
class ConbusRawResponse:
    """Represents a response from Conbus raw telegram send operation.

    Attributes:
        success: Whether the operation was successful.
        sent_telegrams: Raw telegrams sent.
        received_telegrams: List of telegrams received.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.

    """

    success: bool
    sent_telegrams: str | None = None
    received_telegrams: list[str] | None = None
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
            "sent_telegrams": self.sent_telegrams,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
