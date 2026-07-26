# Copyright (c) 2025 ldvchosal
"""Conbus link number response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.utils.time_utils import local_now


@dataclass
class ConbusWriteConfigResponse:
    """Represents a response from Conbus write config operations (set/get).

    Attributes:
        success: Whether the operation was successful.
        serial_number: Serial number of the device.
        datapoint_type: the datapoint to write.
        system_function: ACK or NAK received.
        sent_telegram: Telegram sent to device.
        received_telegrams: List of telegrams received.
        data_value: written value.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.

    """

    success: bool
    serial_number: str
    datapoint_type: DataPointType | None = None
    system_function: SystemFunction | None = None
    sent_telegram: str | None = None
    received_telegrams: list | None = None
    data_value: str | None = None
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
            "system_function": self.system_function,
            "datapoint_type": self.datapoint_type,
            "data_value": self.data_value,
            "serial_number": self.serial_number,
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
