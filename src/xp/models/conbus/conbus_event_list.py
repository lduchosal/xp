"""Conbus event list response model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConbusEventListResponse:
    """Represents a response from Conbus event list operation.

    Attributes:
        events: Dict mapping event keys to list of module names.
        timestamp: Timestamp of the response.
    """

    events: Dict[str, list[str]]
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response.
        """
        return {
            "events": self.events,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
