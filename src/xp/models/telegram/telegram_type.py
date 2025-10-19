"""Telegram type enumeration for console bus communication."""

from enum import Enum


class TelegramType(str, Enum):
    """Enumeration of telegram types in the console bus system.

    Attributes:
        EVENT: Event telegram (E).
        REPLY: Reply telegram (R).
        SYSTEM: System telegram (S).
        CPEVENT: CP event telegram (O).
    """

    EVENT = "E"
    REPLY = "R"
    SYSTEM = "S"
    CPEVENT = "O"
