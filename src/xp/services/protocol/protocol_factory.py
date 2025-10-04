import logging

from bubus import EventBus
from twisted.internet import protocol
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure

from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    InvalidTelegramReceivedEvent,
    ModuleDiscoveredEvent,
    ModuleErrorCodeReadEvent,
    ModuleTypeReadEvent,
    TelegramReceivedEvent,
)
from xp.services.protocol.telegram_protocol import TelegramProtocol

# Rebuild models after TelegramProtocol is imported to resolve forward references
ConnectionMadeEvent.model_rebuild()
InvalidTelegramReceivedEvent.model_rebuild()
ModuleDiscoveredEvent.model_rebuild()
ModuleErrorCodeReadEvent.model_rebuild()
ModuleTypeReadEvent.model_rebuild()
TelegramReceivedEvent.model_rebuild()


class TelegramFactory(protocol.ClientFactory):
    def __init__(
        self,
        event_bus: EventBus,
        telegram_protocol: TelegramProtocol,
    ) -> None:
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol
        self.logger = logging.getLogger(__name__)

    def buildProtocol(self, addr: IAddress) -> TelegramProtocol:
        self.logger.debug(f"buildProtocol: {addr}")
        return self.telegram_protocol

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        self.event_bus.dispatch(ConnectionFailedEvent(reason=str(reason)))
        connector.stop()

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        self.event_bus.dispatch(ConnectionLostEvent(reason=str(reason)))
        connector.stop()
