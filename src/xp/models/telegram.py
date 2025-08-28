from dataclasses import dataclass


@dataclass
class Telegram:
    """
    Represents an abstract telegram from the console bus.
    Can be an EventTelegram, SystemTelegram or ReplyTelegram
    """

    raw_telegram: str

    def __init__(self):
        self.raw_telegram = "some telegram data"

