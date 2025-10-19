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
    Service for querying datapoints from Conbus modules.

    Uses ConbusProtocol to provide datapoint query functionality
    for reading sensor data and module information.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus datapoint service"""
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
        self.logger.debug(f"Connection established, sending {self.raw_input}")
        self.sendFrame(self.raw_input.encode())

    def telegram_sent(self, telegram_sent: str) -> None:
        self.service_response.success = True
        self.service_response.sent_telegrams = telegram_sent
        self.service_response.timestamp = datetime.now()
        self.service_response.received_telegrams = []
        pass

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.service_response.received_telegrams:
            self.service_response.received_telegrams = []
        self.service_response.received_telegrams.append(telegram_received.frame)

        if self.progress_callback:
            self.progress_callback(telegram_received.frame)

    def timeout(self) -> bool:
        self.logger.debug(f"Timeout: {self.timeout_seconds}s")
        if self.finish_callback:
            self.finish_callback(self.service_response)
        return False

    def failed(self, message: str) -> None:
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
        """
        Query a specific datapoint from a module.

        Args:
            serial_number: 10-digit module serial number
            datapoint_type: Type of datapoint to query
            finish_callback: callback function to call when the datapoint is received
            timeout_seconds: timeout in seconds

        Returns:
            ConbusDatapointResponse with operation result and datapoint value
        """

        self.logger.info("Starting query_datapoint")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.raw_input = raw_input
        self.start_reactor()
