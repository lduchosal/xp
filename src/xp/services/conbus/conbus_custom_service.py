"""
Conbus Custom Service for sending custom telegrams to modules.

This service handles custom telegram operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from psygnal import Signal

from xp.models.conbus.conbus_custom import ConbusCustomResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusCustomService:
    """
    Service for sending custom telegrams to Conbus modules.

    Uses ConbusEventProtocol to provide custom telegram functionality
    for sending arbitrary function codes and data to modules.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        telegram_service: Service for parsing telegrams.
        on_finish: Signal emitted when custom operation completes (with response).
    """

    on_finish: Signal = Signal(ConbusCustomResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_service: TelegramService,
    ) -> None:
        """
        Initialize the Conbus custom service.

        Args:
            conbus_protocol: Protocol instance for Conbus communication.
            telegram_service: Service for parsing telegrams.
        """
        self.conbus_protocol = conbus_protocol
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.function_code: str = ""
        self.data: str = ""
        self.service_response: ConbusCustomResponse = ConbusCustomResponse(
            success=False,
            serial_number=self.serial_number,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            f"Connection established, sending custom telegram F{self.function_code}D{self.data}."
        )
        system_function = SystemFunction.from_code(self.function_code)
        if not system_function:
            self.logger.debug(f"Invalid function code F{self.function_code}")
            self.failed(f"Invalid function code {self.function_code}")
            return

        self.conbus_protocol.send_telegram(
            serial_number=self.serial_number,
            telegram_type=TelegramType.SYSTEM,
            system_function=system_function,
            data_value=self.data,
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.sent_telegram = telegram_sent

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

        if (
            not telegram_received.checksum_valid
            or telegram_received.telegram_type != TelegramType.REPLY
            or telegram_received.serial_number != self.serial_number
        ):
            self.logger.debug("Not a reply for our serial number")
            return

        # Parse the reply telegram
        parsed_telegram = self.telegram_service.parse_telegram(telegram_received.frame)
        reply_telegram = None
        if isinstance(parsed_telegram, ReplyTelegram):
            reply_telegram = parsed_telegram

        self.logger.debug("Received reply telegram")
        self.service_response.success = True
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.function_code = self.function_code
        self.service_response.data = self.data
        self.service_response.reply_telegram = reply_telegram

        # Emit finish signal
        self.on_finish.emit(self.service_response)

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Timeout occurred")
        self.failed("Timeout")

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

        # Emit finish signal
        self.on_finish.emit(self.service_response)

    def send_custom_telegram(
        self,
        serial_number: str,
        function_code: str,
        data: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Send a custom telegram to a module.

        Args:
            serial_number: 10-digit module serial number.
            function_code: Function code (e.g., "02", "17").
            data: Data code (e.g., "E2", "AA").
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting send_custom_telegram")
        self.serial_number = serial_number
        self.function_code = function_code
        self.data = data
        if timeout_seconds:
            self.set_timeout(timeout_seconds)

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

    def __enter__(self) -> "ConbusCustomService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.service_response = ConbusCustomResponse(success=False)
        self.serial_number = ""
        self.function_code = ""
        self.data = ""
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
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
