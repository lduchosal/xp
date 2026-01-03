"""Protocol layer services for XP."""

from xp.models.protocol.conbus_protocol import (
    ConnectionMadeEvent,
    EventTelegramReceivedEvent,
    InvalidTelegramReceivedEvent,
    ModuleDiscoveredEvent,
    TelegramReceivedEvent,
)
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

__all__ = ["ConbusEventProtocol"]

# Rebuild models after ConbusEventProtocol is imported to resolve forward references
ConnectionMadeEvent.model_rebuild()
InvalidTelegramReceivedEvent.model_rebuild()
ModuleDiscoveredEvent.model_rebuild()
TelegramReceivedEvent.model_rebuild()
EventTelegramReceivedEvent.model_rebuild()
