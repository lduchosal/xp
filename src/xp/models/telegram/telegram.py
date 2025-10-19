"""Base telegram model for console bus communication."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from xp.models.telegram.telegram_type import TelegramType


@dataclass
class Telegram:
    """Represents an abstract telegram from the console bus.

    Can be an EventTelegram, SystemTelegram or ReplyTelegram.

    Attributes:
        checksum: Telegram checksum value.
        raw_telegram: Raw telegram string.
        checksum_validated: Whether checksum validation passed.
        timestamp: Timestamp when telegram was received.
        telegram_type: Type of telegram (EVENT, SYSTEM, or REPLY).
    """

    checksum: str
    raw_telegram: str
    checksum_validated: Optional[bool] = None
    timestamp: Optional[datetime] = None
    telegram_type: TelegramType = TelegramType.EVENT
