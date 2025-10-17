"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase
from twisted.python.failure import Failure

from xp.models import ConbusClientConfig, ConbusDiscoverResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_protocol import ConbusProtocol


class ConbusDiscoverService(ConbusProtocol):
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus client send service"""
        super().__init__(cli_config, reactor)
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusDiscoverResponse], None]] = None

        self.discovered_device_result = ConbusDiscoverResponse(success=False)
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        self.logger.debug("Connection established, sending discover telegram")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        self.logger.debug(f"Telegram sent: {telegram_sent}")
        self.discovered_device_result.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:

        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.discovered_device_result.received_telegrams:
            self.discovered_device_result.received_telegrams = []
        self.discovered_device_result.received_telegrams.append(telegram_received.frame)

        if (
            telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.checksum_valid
            and telegram_received.payload[11:16] == "F01D"
            and len(telegram_received.payload) == 15
        ):
            self.discovered_device(telegram_received.serial_number)
        else:
            self.logger.debug("Not a discover response")

    def discovered_device(self, serial_number: str) -> None:
        self.logger.info("discovered_device: %s", serial_number)
        if not self.discovered_device_result.discovered_devices:
            self.discovered_device_result.discovered_devices = []
        self.discovered_device_result.discovered_devices.append(serial_number)
        if self.progress_callback:
            self.progress_callback(serial_number)

    def timeout(self) -> None:
        self.logger.info("Discovery stopped after: %ss", self.timeout_seconds)
        self.discovered_device_result.success = True
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)

    def connection_failed(self, reason: Failure) -> None:
        self.logger.debug(f"Client connection failed: {reason}")
        self.discovered_device_result.success = False
        self.discovered_device_result.error = reason.getErrorMessage()
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)

    def start(
        self,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusDiscoverResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop"""
        self.logger.info("Starting discovery")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.start_reactor()
