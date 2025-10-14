"""Telegram Debounce Service for deduplicating protocol requests."""

import asyncio
import logging
from typing import Dict, List, Optional

from bubus import EventBus

from xp.models.protocol.conbus_protocol import ReadDatapointFromProtocolEvent
from xp.models.telegram.system_function import SystemFunction
from xp.services.protocol.telegram_protocol import TelegramProtocol


class TelegramDebounceService:
    """
    Debounces and deduplicates ReadDatapointFromProtocolEvent requests.

    Collects requests in a short time window (default 50ms) and only
    sends unique telegrams to the protocol layer. This prevents duplicate
    telegrams when multiple accessories share the same module.

    Example:
        4 accessories on module 012345678901 trigger cache refresh
        -> 4 ReadDatapointFromProtocolEvent queued
        -> Deduplicated to 1 unique telegram
        -> S012345678901F02D12 sent once (not 4 times)
    """

    def __init__(
        self,
        event_bus: EventBus,
        telegram_protocol: TelegramProtocol,
        debounce_ms: int = 50,
    ) -> None:
        """Initialize the telegram debounce service.

        Args:
            event_bus: EventBus for subscribing to protocol events
            telegram_protocol: TelegramProtocol for sending frames
            debounce_ms: Debounce window in milliseconds (default 50ms)
        """
        self.event_bus = event_bus
        self.telegram_protocol = telegram_protocol
        self.debounce_ms = debounce_ms
        self.logger = logging.getLogger(__name__)

        # Queue of pending requests, keyed by dedup_key
        self.request_queue: Dict[str, List[ReadDatapointFromProtocolEvent]] = {}
        self.timer_handle: Optional[asyncio.TimerHandle] = None

        # Subscribe to protocol events
        self.event_bus.on(
            ReadDatapointFromProtocolEvent, self.handle_read_datapoint_request
        )

        self.logger.info(
            f"TelegramDebounceService initialized with {debounce_ms}ms window"
        )

    def handle_read_datapoint_request(
        self, event: ReadDatapointFromProtocolEvent
    ) -> None:
        """
        Queue request and start/reset debounce timer.

        Args:
            event: ReadDatapointFromProtocolEvent to queue
        """
        # Create dedup key
        dedup_key = self._create_dedup_key(event)

        # Add to queue
        if dedup_key not in self.request_queue:
            self.request_queue[dedup_key] = []
        self.request_queue[dedup_key].append(event)

        queue_size = len(self.request_queue[dedup_key])
        self.logger.debug(f"Queued request: {dedup_key} (queue size: {queue_size})")

        # Reset debounce timer
        if self.timer_handle:
            self.timer_handle.cancel()

        # Schedule queue processing after debounce window
        loop = asyncio.get_event_loop()
        self.timer_handle = loop.call_later(
            self.debounce_ms / 1000.0, lambda: asyncio.create_task(self._process_queue())
        )

    def _create_dedup_key(self, event: ReadDatapointFromProtocolEvent) -> str:
        """
        Create unique key for deduplication.

        Format: "{serial_number}:{datapoint_type_value}"

        Examples:
            012345678901:12 -> OUTPUT_STATE for module 012345678901
            012345678901:15 -> LIGHT_LEVEL for module 012345678901

        Args:
            event: ReadDatapointFromProtocolEvent to create key for

        Returns:
            Deduplication key string
        """
        return f"{event.serial_number}:{event.datapoint_type.value}"

    async def _process_queue(self) -> None:
        """
        Process all queued requests and send unique telegrams.

        Deduplicates requests with the same (serial_number, datapoint_type)
        and sends only one telegram per unique combination.
        """
        if not self.request_queue:
            return

        total_requests = sum(len(events) for events in self.request_queue.values())
        unique_telegrams = len(self.request_queue)
        deduped = total_requests - unique_telegrams

        self.logger.info(
            f"Processing request queue: {unique_telegrams} unique telegrams, "
            f"{total_requests} total requests"
        )

        # Process each unique telegram
        for dedup_key, events in self.request_queue.items():
            if len(events) > 1:
                self.logger.debug(
                    f"Sending telegram for {dedup_key} "
                    f"(consolidating {len(events)} duplicate requests)"
                )
            else:
                self.logger.debug(f"Sending telegram for {dedup_key}")

            # Send telegram only ONCE
            # All events in the list are identical, so use the first one
            event = events[0]
            system_function = SystemFunction.READ_DATAPOINT.value
            datapoint_value = event.datapoint_type.value
            telegram = f"S{event.serial_number}F{system_function}D{datapoint_value}"
            self.telegram_protocol.sendFrame(telegram.encode())

        # Log deduplication statistics
        if deduped > 0:
            reduction_pct = (deduped / total_requests) * 100
            self.logger.info(
                f"Debounce batch: {unique_telegrams} sent, "
                f"{deduped} deduplicated "
                f"({reduction_pct:.1f}% reduction)"
            )

        # Clear queue
        self.request_queue.clear()
        self.timer_handle = None
