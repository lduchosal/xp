import logging
from typing import Any, Optional

from twisted.internet import protocol
from twisted.internet.base import DelayedCall
from twisted.internet.interfaces import IAddress, IConnector
from twisted.internet.posixbase import PosixReactorBase
from twisted.python.failure import Failure

from xp.models import ConbusClientConfig
from xp.models.protocol.conbus_protocol import (
    TelegramReceivedEvent,
)
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.utils import calculate_checksum


class ConbusProtocol(protocol.Protocol, protocol.ClientFactory):
    """
    Twisted protocol for XP telegram communication.
    """

    buffer: bytes

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        self.buffer = b""
        self.logger = logging.getLogger(__name__)
        self.cli_config = cli_config.conbus
        self.reactor = reactor
        self.timeout_seconds = self.cli_config.timeout
        self.timeout_call: Optional[DelayedCall] = None

    def connectionMade(self) -> None:
        self.logger.debug("connectionMade")
        self.connection_established()
        # Start inactivity timeout
        self._reset_timeout()

    def dataReceived(self, data: bytes) -> None:
        self.logger.debug("dataReceived")
        self.buffer += data

        while True:
            start = self.buffer.find(b"<")
            if start == -1:
                break

            end = self.buffer.find(b">", start)
            if end == -1:
                break

            # <S0123450001F02D12FK>
            # <R0123450001F02D12FK>
            # <E12L01I08MAK>
            frame = self.buffer[start : end + 1]  # <S0123450001F02D12FK>
            self.buffer = self.buffer[end + 1 :]
            telegram = frame[1:-1]  # S0123450001F02D12FK
            telegram_type = telegram[0:1].decode()  # S
            payload = telegram[:-2]  # S0123450001F02D12
            checksum = telegram[-2:].decode()  # FK
            serial_number = (
                telegram[1:11] if telegram_type in ("S", "R") else b""
            )  # 0123450001
            calculated_checksum = calculate_checksum(payload.decode(encoding="latin-1"))

            checksum_valid = checksum == calculated_checksum
            if not checksum_valid:
                self.logger.debug(
                    f"Invalid checksum: {checksum}, calculated: {calculated_checksum}"
                )

            self.logger.debug(
                f"frameReceived payload: {payload.decode()}, checksum: {checksum}"
            )

            # Reset timeout on activity
            self._reset_timeout()

            telegram_received = TelegramReceivedEvent(
                protocol=self,
                frame=frame.decode(),
                telegram=telegram.decode(),
                payload=payload.decode(),
                telegram_type=telegram_type,
                serial_number=serial_number,
                checksum=checksum,
                checksum_valid=checksum_valid,
            )
            self.telegram_received(telegram_received)

    def sendFrame(self, data: bytes) -> None:
        """
        Send telegram frame

        Args:
            data: Raw telegram payload (without checksum/framing)
        """
        # Calculate full frame (add checksum and brackets)
        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"

        if not self.transport:
            self.logger.info("Invalid transport")
            raise IOError("Transport is not open")

        self.logger.debug(f"Sending frame: {frame.decode()}")
        self.transport.write(frame)  # type: ignore
        self.telegram_sent(frame.decode())

    def send_telegram(
        self,
        telegram_type: TelegramType,
        serial_number: str,
        system_function: SystemFunction,
        data_value: str,
    ) -> None:
        payload = (
            f"{telegram_type.value}"
            f"{serial_number}"
            f"F{system_function.value}"
            f"D{data_value}"
        )
        self.sendFrame(payload.encode())

    def buildProtocol(self, addr: IAddress) -> protocol.Protocol:
        self.logger.debug(f"buildProtocol: {addr}")
        return self

    def clientConnectionFailed(self, connector: IConnector, reason: Failure) -> None:
        self.logger.debug(f"clientConnectionFailed: {reason}")
        self.connection_failed(reason)
        self._cancel_timeout()
        self._stop_reactor()

    def clientConnectionLost(self, connector: IConnector, reason: Failure) -> None:
        self.logger.debug(f"clientConnectionLost: {reason}")
        self.connection_lost(reason)
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
        self.logger.debug(f"Conbus timeout after {self.timeout_seconds} seconds")
        self.timeout()
        self._stop_reactor()

    def _stop_reactor(self) -> None:
        """Stop the reactor if it's running"""
        if self.reactor.running:
            self.logger.info("Stopping reactor")
            self.reactor.stop()

    def start_reactor(self) -> None:
        """Start the reactor if it's running"""
        # Connect to TCP server
        self.logger.info(
            f"Connecting to TCP server {self.cli_config.ip}:{self.cli_config.port}"
        )
        self.reactor.connectTCP(self.cli_config.ip, self.cli_config.port, self)

        # Run the reactor (which now uses asyncio underneath)
        self.logger.info("Starting reactor event loop...")
        self.reactor.run()

    def __enter__(self) -> "ConbusProtocol":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit - ensure connection is closed"""
        self.logger.debug("Exiting the event loop...")
        self._stop_reactor()

    """Override methods"""

    def telegram_sent(self, telegram_sent: str) -> None:
        pass

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        pass

    def connection_established(self) -> None:
        pass

    def connection_failed(self, reason: Failure) -> None:
        pass

    def connection_lost(self, reason: Failure) -> None:
        pass

    def timeout(self) -> None:
        pass
