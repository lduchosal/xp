"""Conbus Receive Service for receiving telegrams from Conbus servers.

This service uses ConbusEventProtocol to provide receive-only functionality,
allowing clients to receive waiting event telegrams using empty telegram sends.
"""

import asyncio
import logging
from typing import Any, Callable, Optional

from xp.models.conbus.conbus_receive import ConbusReceiveResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConbusReceiveService:
    """
    Service for receiving telegrams from Conbus servers.

    Uses ConbusEventProtocol to provide receive-only functionality
    for collecting waiting event telegrams from the server.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
    """

    conbus_protocol: ConbusEventProtocol

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        """Initialize the Conbus receive service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
        """
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusReceiveResponse], None]] = None
        self.receive_response: ConbusReceiveResponse = ConbusReceiveResponse(
            success=True
        )

        self.conbus_protocol: ConbusEventProtocol = conbus_protocol
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection made event."""
        self.logger.debug("Connection established, waiting for telegrams.")

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        pass

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if self.progress_callback:
            self.progress_callback(telegram_received.frame)

        if not self.receive_response.received_telegrams:
            self.receive_response.received_telegrams = []
        self.receive_response.received_telegrams.append(telegram_received.frame)

    def timeout(self) -> None:
        """Handle timeout event to stop receiving."""
        timeout = self.conbus_protocol.timeout_seconds
        self.logger.info("Receive stopped after: %ss", timeout)
        self.receive_response.success = True
        if self.finish_callback:
            self.finish_callback(self.receive_response)

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug("Failed %s:", message)
        self.receive_response.success = False
        self.receive_response.error = message
        if self.finish_callback:
            self.finish_callback(self.receive_response)

    def init(
        self,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusReceiveResponse], None],
        timeout_seconds: Optional[float] = None,
        event_loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Setup callbacks and timeout for receiving telegrams.

        Args:
            progress_callback: Callback for each received telegram.
            finish_callback: Callback when receiving completes.
            timeout_seconds: Optional timeout in seconds.
            event_loop: Optional event loop to use for async operations.
        """
        self.logger.info("Starting receive")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback

        if event_loop:
            self.conbus_protocol.set_event_loop(event_loop)

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.start_reactor()

    def __enter__(self) -> "ConbusReceiveService":
        """Enter context manager.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.receive_response = ConbusReceiveResponse(success=True)
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
