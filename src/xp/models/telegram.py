from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Telegram:
    """
    Represents an abstract telegram from the console bus.
    Can be an EventTelegram, SystemTelegram or ReplyTelegram
    """

    checksum: str
    raw_telegram: str
    checksum_validated: Optional[bool] = None
    timestamp: Optional[datetime] = None
