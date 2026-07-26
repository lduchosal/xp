# Copyright (c) 2025 ldvchosal
"""Conbus event list response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from xp.utils.time_utils import local_now


@dataclass
class ConbusEventListResponse:
    """Represents a response from Conbus event list operation.

    Attributes:
        events: Dict mapping event keys to list of module names.
        timestamp: Timestamp of the response.

    """

    events: dict[str, list[str]]
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = local_now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response.

        """
        return {
            "events": self.events,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
