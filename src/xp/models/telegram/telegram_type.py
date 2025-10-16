"""Telegram type enumeration for console bus communication."""

from enum import Enum


class TelegramType(str, Enum):
    """Enumeration of telegram types in the console bus system."""

    EVENT = "E"
    REPLY = "R"
    SYSTEM = "S"
    CPEVENT = "O"
