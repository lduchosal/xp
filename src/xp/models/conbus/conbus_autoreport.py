# Copyright (c) 2025 ldvchosal
"""Conbus auto report response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from xp.utils.time_utils import local_now


@dataclass
class ConbusAutoreportResponse:
    """Represents a response from Conbus auto report operations (get/set).

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        auto_report_status: Current auto report status.
        result: Result message from set operation.
        sent_telegram: Telegram sent to device.
        received_telegrams: List of telegrams received.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.

    """

    success: bool
    serial_number: str
    auto_report_status: str | None = None
    result: str | None = None
    sent_telegram: str | None = None
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
        result_dict: dict[str, Any] = {
            "success": self.success,
            "serial_number": self.serial_number,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

        # Include auto_report_status if available
        if self.auto_report_status is not None:
            result_dict["auto_report_status"] = self.auto_report_status

        # Include result for set operations
        if self.result is not None:
            result_dict["result"] = self.result

        # Include telegram details
        if self.sent_telegram is not None:
            result_dict["sent_telegram"] = self.sent_telegram

        if self.received_telegrams is not None:
            result_dict["received_telegrams"] = self.received_telegrams

        return result_dict
