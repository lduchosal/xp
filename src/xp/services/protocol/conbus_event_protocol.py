"""
Conbus Event Protocol for XP telegram communication.

This module implements the Twisted protocol for Conbus communication.
"""

import asyncio
import logging
from queue import SimpleQueue
from random import randint
from threading import Lock
from typing import Any, Callable, Optional

from psygnal import Signal
from twisted.internet import protocol
from twisted.internet.base import DelayedCall
from twisted.internet.interfaces import IAddress, IConnector
from twisted.internet.posixbase import PosixReactorBase
from twisted.python.failure import Failure

from xp.models import ConbusClientConfig, ModuleTypeCode
from xp.models.protocol.conbus_protocol import (
    TelegramReceivedEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services import TelegramService
from xp.utils import calculate_checksum

# Constants
NO_ERROR_CODE = "00"
CHUNK_HEADER_LENGTH = 2  # data_value format: 2-char counter + actiontable chunk


class ConbusEventProtocol(protocol.Protocol, protocol.ClientFactory):
    """
    Twisted protocol for XP telegram communication.

    Attributes:
        buffer: Buffer for incoming telegram data.
        logger: Logger instance for this protocol.
        cli_config: Conbus configuration settings.
        timeout_seconds: Timeout duration in seconds.
        timeout_call: Delayed call handle for timeout management.
        telegram_queue: FIFO queue for outgoing telegrams.
        queue_manager_running: Flag indicating if queue manager is active.
        queue_manager_lock: Lock for thread-safe queue manager access.
        on_connection_made: Signal emitted when connection is established.
        on_connection_lost: Signal emitted when connection is lost.
        on_connection_failed: Signal emitted when connection fails.
        on_client_connection_failed: Signal emitted when client connection fails.
        on_client_connection_lost: Signal emitted when client connection is lost.
        on_send_frame: Signal emitted when a frame is sent.
        on_telegram_sent: Signal emitted when a telegram is sent.
        on_data_received: Signal emitted when data is received.
        on_telegram_received: Signal emitted when a telegram is received.
        on_invalid_telegram_received: Signal emitted when invalid telegram received.
        on_read_datapoint_received: Signal emitted when read datapoint reply received.
        on_actiontable_chunk_received: Signal emitted when actiontable chunk received.
        on_eof_received: Signal emitted when EOF telegram received.
        on_timeout: Signal emitted when timeout occurs.
        on_failed: Signal emitted when operation fails.
        on_start_reactor: Signal emitted when reactor starts.
        on_stop_reactor: Signal emitted when reactor stops.
    """

    buffer: bytes

    telegram_queue: SimpleQueue[bytes] = SimpleQueue()  # FIFO
    queue_manager_running: bool = False
    queue_manager_lock: Lock = Lock()

    on_connection_made: Signal = Signal()
    on_connection_lost: Signal = Signal()
    on_connection_failed: Signal = Signal(Failure)
    on_client_connection_failed: Signal = Signal(Failure)
    on_client_connection_lost: Signal = Signal(Failure)
    on_send_frame: Signal = Signal(bytes)
    on_telegram_sent: Signal = Signal(bytes)
    on_data_received: Signal = Signal(bytes)
    on_telegram_received: Signal = Signal(TelegramReceivedEvent)
    on_invalid_telegram_received: Signal = Signal(TelegramReceivedEvent)
    on_read_datapoint_received: Signal = Signal(ReplyTelegram)
    on_actiontable_chunk_received: Signal = Signal(ReplyTelegram, str)
    on_eof_received: Signal = Signal(ReplyTelegram)

    on_timeout: Signal = Signal()
    on_failed: Signal = Signal(str)
    on_start_reactor: Signal = Signal()
    on_stop_reactor: Signal = Signal()

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
        telegram_service: TelegramService,
    ) -> None:
        """
        Initialize ConbusEventProtocol.

        Args:
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event handling.
            telegram_service: Telegram service for parsing telegrams.
        """
        self.buffer = b""
        self.logger = logging.getLogger(__name__)
        self.cli_config = cli_config.conbus
        self._reactor = reactor
        self.timeout_seconds = self.cli_config.timeout
        self.timeout_call: Optional[DelayedCall] = None
        self.telegram_service = telegram_service

    def connectionMade(self) -> None:
        """
        Handle connection established event.

        Called when TCP connection is successfully established. Starts inactivity
        timeout monitoring.
        """
        self.logger.debug("connectionMade")
        self.on_connection_made.emit()

        # Start inactivity timeout
        self._reset_timeout()

    def wait(self, wait_timeout: Optional[float] = None) -> None:
        """
        Wait for incoming telegrams with optional timeout override.

        Args:
            wait_timeout: Optional timeout in seconds to override default.
        """
        if wait_timeout:
            self.timeout_seconds = wait_timeout
        self._reset_timeout()

    def dataReceived(self, data: bytes) -> None:
        """
        Handle received data from TCP connection.

        Parses incoming telegram frames and dispatches events.

        Args:
            data: Raw bytes received from connection.
        """
        self.logger.debug("dataReceived")
        self.on_data_received.emit(data)
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
                telegram[1:11].decode("latin-1") if telegram_type in ("S", "R") else ""
            )  # 0123450001
            calculated_checksum = calculate_checksum(payload.decode(encoding="latin-1"))

            checksum_valid = checksum == calculated_checksum
            if not checksum_valid:
                self.logger.debug(
                    f"Invalid checksum: {checksum}, calculated: {calculated_checksum}"
                )

            self.logger.debug(
                f"frameReceived payload: {payload.decode('latin-1')}, checksum: {checksum}"
            )

            # Reset timeout on activity
            self._reset_timeout()

            telegram_received = TelegramReceivedEvent(
                protocol=self,
                frame=frame.decode("latin-1"),
                telegram=telegram.decode("latin-1"),
                payload=payload.decode("latin-1"),
                telegram_type=telegram_type,
                serial_number=serial_number,
                checksum=checksum,
                checksum_valid=checksum_valid,
            )
            self.emit_telegram_received(telegram_received)

    def emit_telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Received {telegram_received}")
        self.on_telegram_received.emit(telegram_received)

        # Filter invalid telegrams
        if not telegram_received.checksum_valid:
            self.logger.debug("Filtered: invalid checksum")
            self.on_invalid_telegram_received.emit(telegram_received)
            return

        if telegram_received.telegram_type != TelegramType.REPLY.value:
            self.logger.debug(
                f"Filtered: not a reply (got {telegram_received.telegram_type})"
            )
            self.on_invalid_telegram_received.emit(telegram_received)
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )

        if reply_telegram.system_function == SystemFunction.READ_DATAPOINT:
            self.on_read_datapoint_received.emit(reply_telegram)
            return

        if reply_telegram.system_function == SystemFunction.ACTIONTABLE:
            actiontable_chunk = reply_telegram.data_value[CHUNK_HEADER_LENGTH:]
            self.on_actiontable_chunk_received.emit(reply_telegram, actiontable_chunk)
            return

        if reply_telegram.system_function == SystemFunction.EOF:
            self.on_eof_received.emit(reply_telegram)
            return

    def sendFrame(self, data: bytes) -> None:
        """
        Send telegram frame.

        Args:
            data: Raw telegram payload (without checksum/framing).
        """
        self.on_send_frame.emit(data)

        # Calculate full frame (add checksum and brackets)
        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"

        if not self.transport:
            self.logger.info("Invalid transport, connection closed.")
            self.on_connection_failed.emit(Failure("Invalid transport."))
            return

        self.logger.debug(f"Sending frame: {frame.decode()}")
        self.transport.write(frame)  # type: ignore
        self.on_telegram_sent.emit(frame.decode())
        self._reset_timeout()

    def send_telegram(
        self,
        telegram_type: TelegramType,
        serial_number: str,
        system_function: SystemFunction,
        data_value: str,
    ) -> None:
        """
        Send telegram with specified parameters.

        Args:
            telegram_type: Type of telegram to send.
            serial_number: Device serial number.
            system_function: System function code.
            data_value: Data value to send.
        """
        payload = (
            f"{telegram_type.value}"
            f"{serial_number}"
            f"F{system_function.value}"
            f"D{data_value}"
        )
        self.send_raw_telegram(payload)

    def send_event_telegram(
        self, module_type_code: ModuleTypeCode, link_number: int, input_number: int
    ) -> None:
        """
        Send telegram with specified parameters.

        Args:
            module_type_code: Type code of module.
            link_number: Link number.
            input_number: Input number.
        """
        payload = (
            f"E" f"{module_type_code}" f"L{link_number:02d}" f"I{input_number:02d}"
        )
        self.send_raw_telegram(payload)

    def send_raw_telegram(self, payload: str) -> None:
        """
        Send telegram with specified parameters.

        Args:
            payload: Telegram to send.
        """
        self.telegram_queue.put_nowait(payload.encode())
        self.call_later(0.0, self.start_queue_manager)

    def send_error_status_query(self, serial_number: str) -> None:
        """
        Send error status query telegram.

        Args:
            serial_number: Device serial number.
        """
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=DataPointType.MODULE_ERROR_CODE.value,
        )

    def send_download_request(
        self, serial_number: str, actiontable_type: SystemFunction
    ) -> None:
        """
        Send download request telegram.

        Args:
            serial_number: Device serial number.
            actiontable_type: DOWNLOAD_ACTIONTABLE or DOWNLOAD_MSACTIONTABLE.
        """
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=actiontable_type,
            data_value=NO_ERROR_CODE,
        )

    def send_ack(self, serial_number: str) -> None:
        """
        Send ACK telegram.

        Args:
            serial_number: Device serial number.
        """
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.ACK,
            data_value=NO_ERROR_CODE,
        )

    def call_later(
        self,
        delay: float,
        callable_action: Callable[..., Any],
        *args: object,
        **kw: object,
    ) -> DelayedCall:
        """
        Schedule a callable to be called later.

        Args:
            delay: Delay in seconds before calling.
            callable_action: The callable to execute.
            args: Positional arguments to pass to callable.
            kw: Keyword arguments to pass to callable.

        Returns:
            DelayedCall object that can be cancelled.
        """
        return self._reactor.callLater(delay, callable_action, *args, **kw)

    def buildProtocol(self, addr: IAddress) -> protocol.Protocol:
        """
        Build protocol instance for connection.

        Args:
            addr: Address of the connection.

        Returns:
            Protocol instance for this connection.
        """
        self.logger.debug(f"buildProtocol: {addr}")
        return self

    def clientConnectionFailed(self, _connector: IConnector, reason: Failure) -> None:
        """
        Handle client connection failure.

        Args:
            _connector: Connection connector instance (unused, required by Twisted).
            reason: Failure reason details.
        """
        self.logger.debug(f"clientConnectionFailed: {reason}")
        self.on_client_connection_failed.emit(reason)
        self.connection_failed(reason)
        self._cancel_timeout()

    def clientConnectionLost(self, _connector: IConnector, reason: Failure) -> None:
        """
        Handle client connection lost event.

        Args:
            _connector: Connection connector instance (unused, required by Twisted).
            reason: Reason for connection loss.
        """
        self.logger.debug(f"clientConnectionLost: {reason}")
        self.on_connection_lost.emit(reason)
        self._cancel_timeout()

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.info("Timeout after: %ss", self.timeout_seconds)
        self.on_timeout.emit()

    def connection_failed(self, reason: Failure) -> None:
        """
        Handle connection failure.

        Args:
            reason: Failure reason details.
        """
        self.logger.debug(f"Client connection failed: {reason}")
        self.on_connection_failed.emit(reason)
        self.on_failed.emit(reason.getErrorMessage())

    def _reset_timeout(self) -> None:
        """Reset the inactivity timeout."""
        self._cancel_timeout()
        self.timeout_call = self.call_later(self.timeout_seconds, self._on_timeout)

    def _cancel_timeout(self) -> None:
        """Cancel the inactivity timeout."""
        if self.timeout_call and self.timeout_call.active():
            self.timeout_call.cancel()

    def _on_timeout(self) -> None:
        """Handle inactivity timeout expiration."""
        self.timeout()
        self.logger.debug(f"Conbus timeout after {self.timeout_seconds} seconds")

    def stop_reactor(self) -> None:
        """Stop the reactor if it's running."""
        try:
            if self._reactor.running:
                self.logger.info("Stopping reactor")
                self._reactor.stop()
        except Exception as e:
            # Reactor might have already stopped or not been started via run()
            self.logger.debug(f"Reactor stop failed (likely already stopped): {e}")

    def connect(self) -> None:
        """
        Connect to TCP server.

        Automatically detects and integrates with running asyncio event loop if present.
        """
        self.logger.info(
            f"Connecting to TCP server {self.cli_config.ip}:{self.cli_config.port}"
        )

        # Auto-detect and integrate with asyncio event loop if available
        try:
            event_loop = asyncio.get_running_loop()
            self.logger.debug(f"Detected running event loop: {event_loop}")
            self.set_event_loop(event_loop)
        except RuntimeError:
            # No running event loop - that's fine for non-async contexts
            self.logger.debug("No running event loop detected - using reactor only")

        self._reactor.connectTCP(self.cli_config.ip, self.cli_config.port, self)

    def disconnect(self) -> None:
        """Disconnect from TCP server."""
        self.logger.info("Disconnecting TCP server")
        self._reactor.disconnectAll()

    def start_reactor(self) -> None:
        """Start the reactor if it's running."""
        self.connect()
        # Run the reactor (which now uses asyncio underneath)
        self.logger.info("Starting reactor event loop.")
        self._reactor.run()

    def start_queue_manager(self) -> None:
        """Start the queue manager if it's not running."""
        with self.queue_manager_lock:
            if self.queue_manager_running:
                return
            self.logger.debug("Queue manager: starting")
            self.queue_manager_running = True
            self.process_telegram_queue()

    def process_telegram_queue(self) -> None:
        """Start the queue manager if it's not running."""
        self.logger.debug(
            f"Queue manager: processing (remaining: {self.telegram_queue.qsize()})"
        )
        if self.telegram_queue.empty():
            with self.queue_manager_lock:
                self.logger.debug("Queue manager: stopping")
                self.queue_manager_running = False
                return

        self.logger.debug("Queue manager: event loop")
        telegram = self.telegram_queue.get_nowait()
        self.sendFrame(telegram)
        later = randint(5, self.cli_config.queue_delay_max) / 100
        self.call_later(later, self.process_telegram_queue)

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Change the event loop.

        Args:
            event_loop: the event loop instance.
        """
        reactor = self._reactor
        if hasattr(reactor, "_asyncioEventloop"):
            reactor._asyncioEventloop = event_loop

        # Set reactor to running state
        if not reactor.running:
            reactor.running = True
            if hasattr(reactor, "startRunning"):
                reactor.startRunning()
            self.logger.info("Set reactor to running state")

    def __enter__(self) -> "ConbusEventProtocol":
        """
        Enter context manager.

        Returns:
            Self for context management.
        """
        self.logger.debug("Entering the event loop.")
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit - ensure connection is closed."""
        self.logger.debug("Exiting the event loop.")
        self.stop_reactor()
