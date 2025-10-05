import asyncio
import logging

from bubus import EventBus
from twisted.internet import protocol

from xp.models.protocol.conbus_protocol import (
    ConnectionMadeEvent,
    InvalidTelegramReceivedEvent,
    TelegramReceivedEvent,
)
from xp.utils import calculate_checksum


class TelegramProtocol(protocol.Protocol):
    buffer: bytes
    event_bus: EventBus

    def __init__(self, event_bus: EventBus) -> None:
        self.buffer = b""
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

    def connectionMade(self) -> None:
        self.logger.debug("connectionMade")
        if self.transport:
            peer = self.transport.getPeer()
            self.logger.info(f"TCP connection established to {peer}")
        else:
            self.logger.warning("connectionMade called with no transport")
        # Schedule async handler using asyncio (since we're using asyncio reactor)
        try:
            self.logger.debug("Scheduling async connection handler")
            task = asyncio.create_task(self._async_connectionMade())
            task.add_done_callback(self._on_task_done)
        except Exception as e:
            self.logger.error(f"Error scheduling async handler: {e}", exc_info=True)

    def _on_task_done(self, task: asyncio.Task) -> None:
        """Callback when async task completes"""
        try:
            if task.exception():
                self.logger.error(f"Async task failed: {task.exception()}", exc_info=task.exception())
            else:
                self.logger.debug("Async task completed successfully")
        except Exception as e:
            self.logger.error(f"Error in task done callback: {e}", exc_info=True)

    async def _async_connectionMade(self) -> None:
        """Async handler for connection made"""
        self.logger.debug("_async_connectionMade starting")
        self.logger.info("Dispatching ConnectionMadeEvent")
        try:
            await self.event_bus.dispatch(ConnectionMadeEvent(protocol=self))
            self.logger.debug("ConnectionMadeEvent dispatched successfully")
        except Exception as e:
            self.logger.error(f"Error dispatching ConnectionMadeEvent: {e}", exc_info=True)

    def dataReceived(self, data: bytes) -> None:
        """Sync callback from Twisted - delegates to async implementation"""
        task = asyncio.create_task(self._async_dataReceived(data))
        task.add_done_callback(self._on_task_done)

    async def _async_dataReceived(self, data: bytes) -> None:
        """Async handler for received data"""
        self.logger.debug("dataReceived")
        self.buffer += data

        while True:
            start = self.buffer.find(b"<")
            if start == -1:
                break

            end = self.buffer.find(b">", start)
            if end == -1:
                break

            frame = self.buffer[start + 1 : end]
            self.buffer = self.buffer[end + 1 :]
            payload = frame[:-2].decode()
            payload_checksum = frame[-2:].decode()
            calculated_checksum = calculate_checksum(payload)

            if payload_checksum != calculated_checksum:
                await self.event_bus.dispatch(
                    InvalidTelegramReceivedEvent(protocol=self, telegram=self.buffer)
                )
                self.logger.debug(
                    f"Invalid frame: {frame.decode()} "
                    f"checksum: {payload_checksum}, "
                    f"expected {calculated_checksum}"
                )
                return

            await self._async_frameReceived(frame[:-2])

    async def _async_frameReceived(self, frame: bytes) -> None:
        """Async handler for received frame"""
        self.logger.debug(f"frameReceived {frame.decode()}")
        telegram = frame.decode()
        raw_frame = f"<{frame.decode()}>"

        # Dispatch event to bubus with await
        await self.event_bus.dispatch(
            TelegramReceivedEvent(protocol=self, telegram=telegram, raw_frame=raw_frame)
        )

    def sendFrame(self, data: bytes) -> None:
        self.logger.debug(f"sendFrame {data.decode()}")

        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"
        if not self.transport:
            self.logger.info("Invalid transport")
            return
        self.transport.write(frame)  # type: ignore
