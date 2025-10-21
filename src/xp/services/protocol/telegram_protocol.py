"""Telegram Protocol for XP telegram communication.

This module provides the protocol implementation for telegram-based communication.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional

from bubus import EventBus
from twisted.internet import protocol

from xp.models.protocol.conbus_protocol import (
    ConnectionMadeEvent,
    InvalidTelegramReceivedEvent,
    TelegramReceivedEvent,
)
from xp.utils import calculate_checksum


class TelegramProtocol(protocol.Protocol):
    """Twisted protocol for XP telegram communication with built-in debouncing.

    Automatically deduplicates identical telegram frames sent within a
    configurable time window (default 50ms).

    Attributes:
        buffer: Buffer for incoming telegram data.
        event_bus: Event bus for dispatching protocol events.
        debounce_ms: Debounce time window in milliseconds.
        logger: Logger instance for this protocol.
        send_queue: Dictionary tracking frame send timestamps.
        timer_handle: Handle for cleanup timer.
    """

    buffer: bytes
    event_bus: EventBus

    def __init__(self, event_bus: EventBus, debounce_ms: int = 50) -> None:
        """Initialize TelegramProtocol.

        Args:
            event_bus: Event bus for dispatching protocol events.
            debounce_ms: Debounce time window in milliseconds.
        """
        self.buffer = b""
        self.event_bus = event_bus
        self.debounce_ms = debounce_ms
        self.logger = logging.getLogger(__name__)

        # Debounce state
        self.send_queue: Dict[bytes, List[float]] = {}  # frame -> [timestamps]
        self.timer_handle: Optional[asyncio.TimerHandle] = None

    def connectionMade(self) -> None:
        """Handle connection established event."""
        self.logger.debug("connectionMade")
        try:
            self.logger.debug("Scheduling async connection handler")
            task = asyncio.create_task(self._async_connection_made())
            task.add_done_callback(self._on_task_done)
        except Exception as e:
            self.logger.error(f"Error scheduling async handler: {e}", exc_info=True)

    def _on_task_done(self, task: asyncio.Task) -> None:
        """Handle async task completion.

        Args:
            task: Completed async task.
        """
        try:
            if task.exception():
                self.logger.error(
                    f"Async task failed: {task.exception()}", exc_info=task.exception()
                )
            else:
                self.logger.debug("Async task completed successfully")
        except Exception as e:
            self.logger.error(f"Error in task done callback: {e}", exc_info=True)

    async def _async_connection_made(self) -> None:
        """Async handler for connection made."""
        self.logger.debug("_async_connectionMade starting")
        self.logger.info("Dispatching ConnectionMadeEvent")
        try:
            await self.event_bus.dispatch(ConnectionMadeEvent(protocol=self))
            self.logger.debug("ConnectionMadeEvent dispatched successfully")
        except Exception as e:
            self.logger.error(
                f"Error dispatching ConnectionMadeEvent: {e}", exc_info=True
            )

    def dataReceived(self, data: bytes) -> None:
        """Handle received data from Twisted.

        Args:
            data: Raw bytes received from connection.
        """
        task = asyncio.create_task(self._async_dataReceived(data))
        task.add_done_callback(self._on_task_done)

    async def _async_dataReceived(self, data: bytes) -> None:
        """Async handler for received data."""
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

            if checksum != calculated_checksum:
                self.logger.debug(
                    f"Invalid frame: {frame.decode()} "
                    f"checksum: {checksum}, "
                    f"expected {calculated_checksum}"
                )
                await self.event_bus.dispatch(
                    InvalidTelegramReceivedEvent(
                        protocol=self,
                        frame=frame.decode(),
                        error=f"Invalid checksum ({calculated_checksum} != {checksum})",
                    )
                )
                return

            self.logger.debug(
                f"frameReceived payload: {payload.decode()}, checksum: {checksum}"
            )
            # Dispatch event to bubus with await
            self.logger.debug("frameReceived about to dispatch TelegramReceivedEvent")
            await self.event_bus.dispatch(
                TelegramReceivedEvent(
                    protocol=self,
                    frame=frame.decode("latin-1"),
                    telegram=telegram.decode("latin-1"),
                    payload=payload.decode("latin-1"),
                    telegram_type=telegram_type,
                    serial_number=serial_number,
                    checksum=checksum,
                )
            )
            self.logger.debug(
                "frameReceived TelegramReceivedEvent dispatched successfully"
            )

    def sendFrame(self, data: bytes) -> None:
        """Send telegram frame.

        Args:
            data: Raw telegram payload (without checksum/framing).
        """
        task = asyncio.create_task(self._async_sendFrame(data))
        task.add_done_callback(self._on_task_done)

    async def _async_sendFrame(self, data: bytes) -> None:
        """
        Send telegram frame with automatic deduplication.

        Args:
            data: Raw telegram payload (without checksum/framing)
        """
        # Calculate full frame (add checksum and brackets)
        checksum = calculate_checksum(data.decode())
        frame_data = data.decode() + checksum
        frame = b"<" + frame_data.encode() + b">"

        # Apply debouncing and send
        await self._send_frame_debounce(frame)

    async def _send_frame_debounce(self, frame: bytes) -> None:
        """
        Apply debouncing logic and send frame if not a duplicate.

        Identical frames within debounce_ms window are deduplicated.
        Only the first occurrence is actually sent to the wire.

        Args:
            frame: Complete telegram frame (with checksum and brackets)
        """
        current_time = time.time()

        # Check if identical frame was recently sent
        if frame in self.send_queue:
            recent_sends = [
                ts
                for ts in self.send_queue[frame]
                if current_time - ts < (self.debounce_ms / 1000.0)
            ]

            if recent_sends:
                # Duplicate detected - skip sending
                self.logger.debug(
                    f"Debounced duplicate frame: {frame.decode()} "
                    f"(sent {len(recent_sends)} times in last {self.debounce_ms}ms)"
                )
                return

        # Not a duplicate - send it
        await self._send_frame_immediate(frame)

        # Track this send
        if frame not in self.send_queue:
            self.send_queue[frame] = []
        self.send_queue[frame].append(current_time)

        # Schedule cleanup of old timestamps
        self._schedule_cleanup()

    async def _send_frame_immediate(self, frame: bytes) -> None:
        """Actually send frame to TCP transport."""
        if not self.transport:
            self.logger.info("Invalid transport")
            raise IOError("Transport is not open")

        self.logger.debug(f"Sending frame: {frame.decode()}")
        self.transport.write(frame)  # type: ignore

    def _schedule_cleanup(self) -> None:
        """Schedule cleanup of old timestamp tracking."""
        if self.timer_handle:
            self.timer_handle.cancel()

        loop = asyncio.get_event_loop()
        self.timer_handle = loop.call_later(
            (self.debounce_ms / 1000.0) * 2,  # Cleanup after 2x debounce window
            self._cleanup_old_timestamps,
        )

    def _cleanup_old_timestamps(self) -> None:
        """Remove old timestamps to prevent memory leak."""
        current_time = time.time()
        cutoff = current_time - (self.debounce_ms / 1000.0)

        for frame in list(self.send_queue.keys()):
            # Keep only recent timestamps
            self.send_queue[frame] = [
                ts for ts in self.send_queue[frame] if ts >= cutoff
            ]

            # Remove frame if no recent sends
            if not self.send_queue[frame]:
                del self.send_queue[frame]

        self.timer_handle = None
