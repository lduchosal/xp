"""
Conbus Scan Service for TCP communication with Conbus servers.

This service implements a TCP client that scans Conbus servers and sends telegrams to
scan modules for all datapoints by function code.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from psygnal import Signal

from xp.models import ConbusResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ConbusScanService:
    """
    Service for scanning modules for all datapoints by function code.

    Uses ConbusEventProtocol to provide scan functionality for discovering
    all available datapoints on a module.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        on_progress: Signal emitted when scan progress is made (with telegram frame).
        on_finish: Signal emitted when scan finishes (with result).
    """

    on_progress: Signal = Signal(str)
    on_finish: Signal = Signal(ConbusResponse)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
    ) -> None:
        """
        Initialize the Conbus scan service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
        """
        self.conbus_protocol = conbus_protocol
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

        self.serial_number: str = ""
        self.function_code: str = ""
        self.datapoint_value: int = -1
        self.service_response: ConbusResponse = ConbusResponse(
            success=False,
            serial_number=self.serial_number,
            sent_telegrams=[],
            received_telegrams=[],
            timestamp=datetime.now(),
        )
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_made(self) -> None:
        """Handle connection made event."""
        self.logger.debug("Connection established, starting scan")
        self.scan_next_datacode()

    def scan_next_datacode(self) -> bool:
        """
        Scan the next data code.

        Returns:
            True if scanning should continue, False if complete.
        """
        self.datapoint_value += 1
        if self.datapoint_value >= 100:
            self.on_finish.emit(self.service_response)
            return False

        self.logger.debug(f"Scanning next datacode: {self.datapoint_value:02d}")
        data = f"{self.datapoint_value:02d}"
        telegram_body = f"S{self.serial_number}F{self.function_code}D{data}"
        self.conbus_protocol.sendFrame(telegram_body.encode())
        return True

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.success = True
        self.service_response.sent_telegrams.append(telegram_sent)

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
        """Handle timeout event by scanning next data code."""
        timeout_seconds = self.conbus_protocol.timeout_seconds
        self.logger.debug(f"Timeout: {timeout_seconds}s")
        self.scan_next_datacode()

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

    def scan_module(
        self,
        serial_number: str,
        function_code: str,
        timeout_seconds: float = 0.25,
    ) -> None:
        """
        Scan a module for all datapoints by function code.

        Args:
            serial_number: 10-digit module serial number.
            function_code: The function code to scan.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting scan_module")
        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds

        self.serial_number = serial_number
        self.function_code = function_code

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

    def __enter__(self) -> "ConbusScanService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.serial_number = ""
        self.function_code = ""
        self.datapoint_value = -1
        self.service_response = ConbusResponse(
            success=False,
            serial_number="",
            sent_telegrams=[],
            received_telegrams=[],
            timestamp=datetime.now(),
        )
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
