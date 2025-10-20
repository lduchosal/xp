"""Conbus Discover Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
discover telegrams to find modules on the network.
"""

import logging
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig, ConbusDiscoverResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_protocol import ConbusProtocol


class ConbusDiscoverService(ConbusProtocol):
    """
    Service for discovering modules on Conbus servers.

    Uses ConbusProtocol to provide discovery functionality for finding
    modules connected to the Conbus network.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus discover service.

        Args:
            cli_config: Conbus client configuration.
            reactor: Twisted reactor instance.
        """
        super().__init__(cli_config, reactor)
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[ConbusDiscoverResponse], None]] = None

        self.discovered_device_result = ConbusDiscoverResponse(success=False)
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, sending discover telegram")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.logger.debug(f"Telegram sent: {telegram_sent}")
        self.discovered_device_result.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.discovered_device_result.received_telegrams:
            self.discovered_device_result.received_telegrams = []
        self.discovered_device_result.received_telegrams.append(telegram_received.frame)

        if (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY.value
            and telegram_received.payload[11:16] == "F01D"
            and len(telegram_received.payload) == 15
        ):
            self.discovered_device(telegram_received.serial_number)
        else:
            self.logger.debug("Not a discover response")

    def discovered_device(self, serial_number: str) -> None:
        """Handle discovered device event.

        Args:
            serial_number: Serial number of the discovered device.
        """
        self.logger.info("discovered_device: %s", serial_number)
        if not self.discovered_device_result.discovered_devices:
            self.discovered_device_result.discovered_devices = []
        self.discovered_device_result.discovered_devices.append(serial_number)
        if self.progress_callback:
            self.progress_callback(serial_number)

    def timeout(self) -> bool:
        """Handle timeout event to stop discovery.

        Returns:
            False to stop the reactor.
        """
        self.logger.info("Discovery stopped after: %ss", self.timeout_seconds)
        self.discovered_device_result.success = True
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)
        return False

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.discovered_device_result.success = False
        self.discovered_device_result.error = message
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)

    def start(
        self,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[ConbusDiscoverResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            progress_callback: Callback for each discovered device.
            finish_callback: Callback when discovery completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting discovery")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.start_reactor()
