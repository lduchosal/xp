"""Conbus Receive Service for receiving telegrams from Conbus servers.

This service uses composition with ConbusService to provide receive-only functionality,
allowing clients to receive waiting event telegrams using empty telegram sends.
"""

import logging
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase
from twisted.python.failure import Failure

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_receive import ConbusReceiveResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol import ConbusProtocol


class ConbusReceiveService(ConbusProtocol):
    """
    Service for receiving telegrams from Conbus servers.

    Uses composition with ConbusService to provide receive-only functionality
    for collecting waiting event telegrams from the server.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus client send service"""
        super().__init__(cli_config, reactor)
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusReceiveResponse], None]] = None
        self.receive_response: ConbusReceiveResponse = ConbusReceiveResponse(
            success=True
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        self.logger.debug("Connection established, waiting for telegrams...")

    def telegram_sent(self, telegram_sent: str) -> None:
        pass

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:

        self.logger.debug(f"Telegram received: {telegram_received}")
        if self.progress_callback:
            self.progress_callback(telegram_received.frame)

        if not self.receive_response.received_telegrams:
            self.receive_response.received_telegrams = []
        self.receive_response.received_telegrams.append(telegram_received.frame)

    def timeout(self) -> None:
        self.logger.info("Discovery stopped after: %ss", self.timeout_seconds)
        if self.finish_callback:
            self.finish_callback(self.receive_response)

    def connection_failed(self, reason: Failure) -> None:
        self.logger.debug(f"Client connection failed: {reason}")
        self.receive_response.success = False
        self.receive_response.error = reason.getErrorMessage()
        if self.finish_callback:
            self.finish_callback(self.receive_response)

    def start(
        self,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusReceiveResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop"""
        self.logger.info("Starting discovery")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.start_reactor()
