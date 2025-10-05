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

            frame = self.buffer[start : end+1]
            self.buffer = self.buffer[end + 1 :]
            telegram = frame[1:-1]
            payload = telegram[:-2].decode()
            serial_number = telegram[1:11].decode()
            checksum = telegram[-2:].decode()
            calculated_checksum = calculate_checksum(payload)

            if checksum != calculated_checksum:
                await self.event_bus.dispatch(
                    InvalidTelegramReceivedEvent(
                        protocol=self,
                        frame=frame.decode(),
                        telegram=telegram.decode(),
                        payload=payload,
                        serial_number=serial_number,
                        checksum=checksum,
                        error="Invalid checksum"
                    )
                )
                self.logger.debug(
                    f"Invalid frame: {frame.decode()} "
                    f"checksum: {checksum}, "
                    f"expected {calculated_checksum}"
                )
                return

            self.logger.debug(f"frameReceived payload: {payload}, checksum: {checksum}")

            # Dispatch event to bubus with await
            self.logger.debug(f"frameReceived about to dispatch TelegramReceivedEvent")
            await self.event_bus.dispatch(
                TelegramReceivedEvent(
                    protocol=self,
                    frame=frame.decode(),
                    telegram=telegram.decode(),
                    payload=payload,
                    serial_number=serial_number,
                    checksum=checksum
                )
            )
            self.logger.debug(f"frameReceived TelegramReceivedEvent dispatched successfully")


    def sendFrame(self, data: bytes) -> None:
        self.logger.debug(f"sendFrame {data.decode()}")

        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"
        if not self.transport:
            self.logger.info("Invalid transport")
            raise IOError("Transport is not open")
        self.transport.write(frame)  # type: ignore
