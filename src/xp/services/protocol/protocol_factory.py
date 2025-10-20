"""Protocol Factory for Twisted protocol creation.

This module provides factory classes for protocol instantiation.
"""

import logging

from bubus import EventBus
from twisted.internet import protocol
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure

from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
)
from xp.services.protocol import TelegramProtocol


class TelegramFactory(protocol.ClientFactory):
    """Factory for creating Telegram protocol instances.

    Attributes:
        event_bus: Event bus for dispatching protocol events.
        telegram_protocol: Protocol instance to use.
        connector: Connection connector instance.
        logger: Logger instance for this factory.
    """

    def __init__(
        self,
        event_bus: EventBus,
        telegram_protocol: TelegramProtocol,
        connector: IConnector,
    ) -> None:
        """Initialize TelegramFactory.

        Args:
            event_bus: Event bus for protocol events.
            telegram_protocol: Protocol instance to use for connections.
            connector: Connection connector for managing connections.
        """
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol
        self.connector = connector
        self.logger = logging.getLogger(__name__)

    def buildProtocol(self, addr: IAddress) -> TelegramProtocol:
        """Build protocol instance for connection.

        Args:
            addr: Address of the connection.

        Returns:
            Telegram protocol instance for this connection.
        """
        self.logger.debug(f"buildProtocol: {addr}")
        return self.telegram_protocol

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        """Handle connection failure event.

        Args:
            connector: Connection connector instance.
            reason: Failure reason details.
        """
        self.event_bus.dispatch(ConnectionFailedEvent(reason=str(reason)))
        self.connector.stop()

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        """Handle connection lost event.

        Args:
            connector: Connection connector instance.
            reason: Reason for connection loss.
        """
        self.event_bus.dispatch(ConnectionLostEvent(reason=str(reason)))
        self.connector.stop()
