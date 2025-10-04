from __future__ import annotations

from typing import TYPE_CHECKING

from bubus import BaseEvent
from pydantic import Field

if TYPE_CHECKING:
    from xp.services.protocol.telegram_protocol import TelegramProtocol


class ConnectionMadeEvent(BaseEvent):
    """Event dispatched when TCP connection is established"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )


class ConnectionFailedEvent(BaseEvent):
    """Event dispatched when TCP connection fails"""

    reason: str = Field(description="Failure reason")


class ConnectionLostEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    reason: str = Field(description="Disconnection reason")


class ModuleDiscoveredEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )
    telegram: str = Field(description="The received telegram payload")


class ModuleTypeReadEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )
    telegram: str = Field(description="The received telegram payload")


class ModuleErrorCodeReadEvent(BaseEvent):
    """Event dispatched when TCP connection is lost"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )
    telegram: str = Field(description="The received telegram payload")


class TelegramReceivedEvent(BaseEvent):
    """Event dispatched when a telegram frame is received"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )
    telegram: str = Field(description="The received telegram payload")
    raw_frame: str = Field(description="The raw frame with delimiters")


class InvalidTelegramReceivedEvent(BaseEvent):
    """Event dispatched when a telegram frame is received"""

    protocol: TelegramProtocol = Field(
        description="Reference to the TelegramProtocol instance"
    )
    telegram: str = Field(description="The received telegram payload")
