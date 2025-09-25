"""Log entry model for console bus communication logs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union, Any

from .event_telegram import EventTelegram
from .reply_telegram import ReplyTelegram
from .system_telegram import SystemTelegram


@dataclass
class LogEntry:
    """
    Represents a single entry in a console bus log file.

    Format: HH:MM:SS,mmm [TX/RX] <telegram>
    Examples: 22:44:20,352 [TX] <S0012345008F27D00AAFN>
    """

    timestamp: datetime
    direction: str  # "TX" or "RX"
    raw_telegram: str
    parsed_telegram: Optional[Union[EventTelegram, SystemTelegram, ReplyTelegram]] = (
        None
    )
    parse_error: Optional[str] = None
    line_number: int = 0

    @property
    def is_transmitted(self) -> bool:
        """True if this is a transmitted telegram"""
        return self.direction == "TX"

    @property
    def is_received(self) -> bool:
        """True if this is a received telegram"""
        return self.direction == "RX"

    @property
    def telegram_type(self) -> str:
        """Get the telegram type (event, system, reply, unknown)"""
        if self.parsed_telegram is None:
            return "unknown"

        return self.parsed_telegram.telegram_type.value.lower()

    @property
    def is_valid_parse(self) -> bool:
        """True if the telegram was successfully parsed"""
        return self.parsed_telegram is not None and self.parse_error is None

    @property
    def checksum_validated(self) -> Optional[bool]:
        """Get checksum validation status if available"""
        if self.parsed_telegram and hasattr(self.parsed_telegram, "checksum_validated"):
            return self.parsed_telegram.checksum_validated
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result: dict[str, Any] = {
            "line_number": self.line_number,
            "timestamp": self.timestamp.strftime("%H:%M:%S.%f")[
                :-3
            ],  # HH:MM:SS,mmm format
            "direction": self.direction,
            "raw_telegram": self.raw_telegram,
            "telegram_type": self.telegram_type,
            "is_valid_parse": self.is_valid_parse,
            "parse_error": self.parse_error,
        }

        # Add parsed telegram data if available
        if self.parsed_telegram:
            result["parsed"] = self.parsed_telegram.to_dict()
            result["checksum_validated"] = self.checksum_validated

        return result

    def __str__(self) -> str:
        """Human-readable string representation"""
        timestamp_str = self.timestamp.strftime("%H:%M:%S,%f")[:-3]  # HH:MM:SS,mmm
        status = "✓" if self.is_valid_parse else "✗"
        checksum_status = ""

        if self.checksum_validated is not None:
            checksum_status = f" ({('✓' if self.checksum_validated else '✗')})"

        return f"[{self.line_number:3d}] {timestamp_str} [{self.direction}] {self.raw_telegram} {status}{checksum_status}"
