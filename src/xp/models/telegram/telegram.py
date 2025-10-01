from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from xp.models.telegram.telegram_type import TelegramType


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
    telegram_type: TelegramType = TelegramType.EVENT
