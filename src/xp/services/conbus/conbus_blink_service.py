"""
Conbus Blink Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
blink/unblink telegrams to control module LED indicators.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from psygnal import Signal

from xp.models.conbus.conbus_blink import ConbusBlinkResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusBlinkService:
    """
    Service for blinking module LEDs on Conbus servers.

    Uses ConbusEventProtocol to provide blink/unblink functionality
    for controlling module LED indicators.

    Attributes:
        on_finish: Signal emitted when blink operation completes (with response).
    """

    on_finish: Signal = Signal(ConbusBlinkResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        telegram_service: TelegramService,
    ) -> None:
        """
        Initialize the Conbus blink service.

        Args:
            conbus_protocol: ConbusEventProtocol instance for communication.
            telegram_service: Service for parsing telegrams.
        """
        self.conbus_protocol = conbus_protocol
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.on_or_off = "none"
        self.service_response: ConbusBlinkResponse = ConbusBlinkResponse(
            success=False,
            serial_number=self.serial_number,
            system_function=SystemFunction.NONE,
            operation=self.on_or_off,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Connect signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection made event."""
        self.logger.debug("Connection established, sending blink command.")
        # Blink is 05, Unblink is 06
        system_function = SystemFunction.UNBLINK
        if self.on_or_off.lower() == "on":
            system_function = SystemFunction.BLINK

        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=system_function,
            data_value="00",
        )
        self.service_response.system_function = system_function
        self.service_response.operation = self.on_or_off

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        system_telegram = self.telegram_service.parse_system_telegram(telegram_sent)
        self.service_response.sent_telegram = system_telegram

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
            self.logger.debug("Not a reply")
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )
        if reply_telegram is not None and reply_telegram.system_function in (
            SystemFunction.ACK,
            SystemFunction.NAK,
        ):
            self.logger.debug("Received blink response")
            self.service_response.success = True
            self.service_response.timestamp = datetime.now()
            self.service_response.serial_number = self.serial_number
            self.service_response.reply_telegram = reply_telegram

            self.on_finish.emit(self.service_response)

    def timeout(self) -> None:
        """Handle timeout event to stop operation."""
        self.logger.info("Blink operation timeout")
        self.service_response.success = False
        self.service_response.error = "Blink operation timeout"
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

    def send_blink_telegram(
        self,
        serial_number: str,
        on_or_off: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        r"""
        Send blink command to start blinking module LED.

        Args:
            serial_number: 10-digit module serial number.
            on_or_off: "on" to blink or "off" to unblink.
            timeout_seconds: Timeout in seconds.

        Examples:
            \b
            xp conbus blink 0012345008 on
            xp conbus blink 0012345008 off
        """
        self.logger.info("Starting send_blink_telegram")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.on_or_off = on_or_off
        # Caller invokes start_reactor()

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

    def __enter__(self) -> "ConbusBlinkService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.service_response = ConbusBlinkResponse(
            success=False,
            serial_number="",
            system_function=SystemFunction.NONE,
            operation="none",
        )
        self.serial_number = ""
        self.on_or_off = "none"
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager - cleanup signals and reactor."""
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
