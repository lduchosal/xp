"""Conbus Scan Service for TCP communication with Conbus servers.

This service implements a TCP client that scans Conbus servers and sends
telegrams to scan modules for all datapoints by function code.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import (
    ConbusClientConfig,
    ConbusResponse,
)
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.services.protocol import ConbusProtocol


class ConbusScanService(ConbusProtocol):
    """
    Service for scanning modules for all datapoints by function code.

    Uses ConbusProtocol to provide scan functionality for discovering
    all available datapoints on a module.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus scan service.

        Args:
            cli_config: Conbus client configuration.
            reactor: Twisted reactor instance.
        """
        super().__init__(cli_config, reactor)
        self.serial_number: str = ""
        self.function_code: str = ""
        self.datapoint_value: int = -1
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusResponse], None]] = None
        self.service_response: ConbusResponse = ConbusResponse(
            success=False,
            serial_number=self.serial_number,
            sent_telegrams=[],
            received_telegrams=[],
            timestamp=datetime.now(),
        )
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, starting scan")
        self.scan_next_datacode()

    def scan_next_datacode(self) -> bool:
        """Scan the next data code.

        Returns:
            True if scanning should continue, False if complete.
        """
        self.datapoint_value += 1
        if self.datapoint_value >= 100:
            if self.finish_callback:
                self.finish_callback(self.service_response)
            return False

        self.logger.debug(f"Scanning next datacode: {self.datapoint_value:02d}")
        data = f"{self.datapoint_value:02d}"
        telegram_body = f"S{self.serial_number}F{self.function_code}D{data}"
        self.sendFrame(telegram_body.encode())
        return True

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.service_response.success = True
        self.service_response.sent_telegrams.append(telegram_sent)

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
        """Handle timeout event by scanning next data code.

        Returns:
            True to continue scanning, False to stop.
        """
        self.logger.debug(f"Timeout: {self.timeout_seconds}s")
        continue_scan = self.scan_next_datacode()
        return continue_scan

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

    def scan_module(
        self,
        serial_number: str,
        function_code: str,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusResponse], None],
        timeout_seconds: float = 0.25,
    ) -> None:
        """Scan a module for all datapoints by function code.

        Args:
            serial_number: 10-digit module serial number.
            function_code: The function code to scan.
            progress_callback: Callback to handle progress.
            finish_callback: Callback function to call when the scan is complete.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting scan_module")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds

        self.serial_number = serial_number
        self.function_code = function_code
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.start_reactor()
