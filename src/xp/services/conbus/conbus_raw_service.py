"""Conbus Raw Service for sending raw telegram sequences.

This service handles sending raw telegram strings without prior validation.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_raw import ConbusRawResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol import ConbusProtocol


class ConbusRawService(ConbusProtocol):
    """
    Service for sending raw telegram sequences to Conbus modules.

    Uses ConbusProtocol to provide raw telegram functionality
    for sending arbitrary telegram strings without validation.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus raw service.

        Args:
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event loop.
        """
        super().__init__(cli_config, reactor)
        self.raw_input: str = ""
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusRawResponse], None]] = None
        self.service_response: ConbusRawResponse = ConbusRawResponse(
            success=False,
        )
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug(f"Connection established, sending {self.raw_input}")
        self.sendFrame(self.raw_input.encode())

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.success = True
        self.service_response.sent_telegrams = telegram_sent
        self.service_response.timestamp = datetime.now()
        self.service_response.received_telegrams = []

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.service_response.received_telegrams:
            self.service_response.received_telegrams = []
        self.service_response.received_telegrams.append(telegram_received.frame)

        if self.progress_callback:
            self.progress_callback(telegram_received.frame)

    def timeout(self) -> bool:
        """Handle timeout event.

        Returns:
            False to indicate connection should be closed.
        """
        self.logger.debug(f"Timeout: {self.timeout_seconds}s")
        if self.finish_callback:
            self.finish_callback(self.service_response)
        return False

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def send_raw_telegram(
        self,
        raw_input: str,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusRawResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Send a raw telegram string to the Conbus server.

        Args:
            raw_input: Raw telegram string to send.
            progress_callback: Callback to handle progress updates.
            finish_callback: Callback function to call when the operation is complete.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting send_raw_telegram")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.raw_input = raw_input
        self.start_reactor()
