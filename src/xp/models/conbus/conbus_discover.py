# Copyright (c) 2025 ldvchosal
"""Conbus discover response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict

from xp.utils.time_utils import local_now


class DiscoveredDevice(TypedDict):
    """Discovered device information.

    Attributes:
        serial_number: Serial number of the device.
        module_type: Module type name (e.g., "XP24", "XP230"),
            None if not yet retrieved.
        module_type_code: Module type code (e.g., "13", "10"),
            None if not yet retrieved.
        module_type_name: Module type name converted from module_type_code,
            None if not yet retrieved.

    """

    serial_number: str
    module_type: str | None
    module_type_code: int | None
    module_type_name: str | None


@dataclass
class ConbusDiscoverResponse:
    """Represents a response from Conbus send operation.

    Attributes:
        success: Whether the operation was successful.
        sent_telegram: Telegram sent to discover devices.
        received_telegrams: List of telegrams received.
        discovered_devices: List of discovered devices with their module types.
        error: Error message if operation failed.
        timestamp: Timestamp of the response.

    """

    success: bool
    sent_telegram: str | None = None
    received_telegrams: list[str] | None = None
    discovered_devices: list[DiscoveredDevice] | None = None
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
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "discovered_devices": self.discovered_devices,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
