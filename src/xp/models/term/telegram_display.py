"""Domain models for telegram display in terminal interface."""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class TelegramDisplayEvent:
    """Event containing telegram data for display in TUI.

    Attributes:
        direction: Direction of telegram ("RX" for received, "TX" for transmitted).
        telegram: Formatted telegram string.
        timestamp: Optional timestamp of the event.
    """

    direction: Literal["RX", "TX"]
    telegram: str
    timestamp: Optional[float] = None
