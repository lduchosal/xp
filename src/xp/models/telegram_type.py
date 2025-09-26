"""Telegram type enumeration for console bus communication."""

from enum import Enum


class TelegramType(Enum):
    """Enumeration of telegram types in the console bus system."""

    EVENT = "event"
    REPLY = "reply"
    SYSTEM = "system"
