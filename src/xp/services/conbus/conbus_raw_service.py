"""
Conbus Raw Service for sending raw telegram sequences.

This service handles sending raw telegram strings without prior validation.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from psygnal import Signal

from xp.models.conbus.conbus_raw import ConbusRawResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConbusRawService:
    """
    Service for sending raw telegram sequences to Conbus modules.

    Uses ConbusEventProtocol to provide raw telegram functionality
    for sending arbitrary telegram strings without validation.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        on_progress: Signal emitted when telegram is received (with frame).
        on_finish: Signal emitted when operation finishes (with result).
    """

    conbus_protocol: ConbusEventProtocol
    on_progress: Signal = Signal(str)
    on_finish: Signal = Signal(ConbusRawResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
    ) -> None:
        """
        Initialize the Conbus raw service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
        """
        self.conbus_protocol = conbus_protocol

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        self.raw_input: str = ""
        self.service_response: ConbusRawResponse = ConbusRawResponse(
            success=False,
        )
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug(f"Connection established, sending {self.raw_input}")
        self.conbus_protocol.send_raw_telegram(self.raw_input)

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.success = True
        self.service_response.sent_telegrams = telegram_sent
        self.service_response.timestamp = datetime.now()
        self.service_response.received_telegrams = []

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.service_response.received_telegrams:
            self.service_response.received_telegrams = []
        self.service_response.received_telegrams.append(telegram_received.frame)

        self.on_progress.emit(telegram_received.frame)

    def timeout(self) -> None:
        """Handle timeout event."""
        timeout_seconds = self.conbus_protocol.timeout_seconds
        self.logger.debug(f"Timeout: {timeout_seconds}s")
        self.on_finish.emit(self.service_response)

    def failed(self, message: str) -> None:
        """
        Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message
        self.on_finish.emit(self.service_response)

    def send_raw_telegram(
        self,
        raw_input: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Send a raw telegram string to the Conbus server.

        Args:
            raw_input: Raw telegram string to send.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting send_raw_telegram")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.raw_input = raw_input

    def set_timeout(self, timeout_seconds: float) -> None:
        """
        Set operation timeout.

        Args:
            timeout_seconds: Timeout in seconds.
        """
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.start_reactor()

    def stop_reactor(self) -> None:
        """Stop the reactor."""
        self.conbus_protocol.stop_reactor()

    def __enter__(self) -> "ConbusRawService":
        """
        Enter context manager.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.service_response = ConbusRawResponse(success=False)
        self.raw_input = ""
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        # Disconnect protocol signals
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        # Disconnect service signals
        self.on_progress.disconnect()
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
