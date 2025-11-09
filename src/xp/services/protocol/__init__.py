"""Protocol layer services for XP."""

from xp.models.protocol.conbus_protocol import (
    ConnectionMadeEvent,
    EventTelegramReceivedEvent,
    InvalidTelegramReceivedEvent,
    ModuleDiscoveredEvent,
    TelegramReceivedEvent,
)
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.protocol.conbus_protocol import ConbusProtocol
from xp.services.protocol.telegram_protocol import TelegramProtocol

__all__ = ["TelegramProtocol", "ConbusProtocol", "ConbusEventProtocol"]

# Rebuild models after TelegramProtocol and ConbusProtocol are imported to resolve forward references
ConnectionMadeEvent.model_rebuild()
InvalidTelegramReceivedEvent.model_rebuild()
ModuleDiscoveredEvent.model_rebuild()
TelegramReceivedEvent.model_rebuild()
EventTelegramReceivedEvent.model_rebuild()
