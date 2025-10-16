"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
from typing import Callable, Optional

from twisted.internet import protocol
from twisted.internet.base import DelayedCall
from twisted.internet.interfaces import IAddress, IConnector
from twisted.internet.posixbase import PosixReactorBase
from twisted.python.failure import Failure

from xp.models import ConbusClientConfig
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_protocol import ConbusProtocol


class ConbusDiscoverService(ConbusProtocol, protocol.ClientFactory):
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
        timeout_seconds: float = 0.5,
    ) -> None:
        """Initialize the Conbus client send service"""
        super().__init__()
        self.cli_config = cli_config.conbus
        self.reactor = reactor
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[Callable[[list[str]], None]] = None

        self.timeout_seconds = timeout_seconds
        self.timeout_call: Optional[DelayedCall] = None
        self.discovered_device_result: list[str] = []
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
        # Start inactivity timeout
        self._reset_timeout()

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:

        self.logger.debug(f"Telegram received: {telegram_received}")
        # Reset timeout on activity
        self._reset_timeout()

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
        self.discovered_device_result.append(serial_number)
        if self.progress_callback:
            self.progress_callback(serial_number)

    def buildProtocol(self, addr: IAddress) -> ConbusProtocol:
        self.logger.debug(f"buildProtocol: {addr}")
        return self

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        self.logger.debug(f"clientConnectionFailed: {reason}")
        self._cancel_timeout()
        self._stop_reactor()

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        self.logger.debug(f"clientConnectionLost: {reason}")
        self._cancel_timeout()
        self._stop_reactor()

    def _reset_timeout(self) -> None:
        """Reset the inactivity timeout"""
        self._cancel_timeout()
        self.timeout_call = self.reactor.callLater(
            self.timeout_seconds, self._on_timeout
        )
        self.logger.debug(f"Timeout set for {self.timeout_seconds} seconds")

    def _cancel_timeout(self) -> None:
        """Cancel the inactivity timeout"""
        if self.timeout_call and self.timeout_call.active():
            self.timeout_call.cancel()
            self.logger.debug("Timeout cancelled")

    def _on_timeout(self) -> None:
        """Called when inactivity timeout expires"""
        self.logger.info(f"Discovery timeout after {self.timeout_seconds} seconds")
        if self.finish_callback:
            self.finish_callback(self.discovered_device_result)
        self._stop_reactor()

    def _stop_reactor(self) -> None:
        """Stop the reactor if it's running"""
        if self.reactor.running:
            self.logger.info("Stopping reactor")
            self.reactor.stop()

    def run(
        self,
        progress_callback: Callable[[str], None],
        finish_callback: Callable[[list[str]], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop"""
        self.logger.info("Starting discovery")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        # Connect to TCP server
        self.logger.info(
            f"Connecting to TCP server {self.cli_config.ip}:{self.cli_config.port}"
        )
        self.reactor.connectTCP(self.cli_config.ip, self.cli_config.port, self)

        # Run the reactor (which now uses asyncio underneath)
        self.logger.info("Starting reactor event loop...")
        self.reactor.run()
