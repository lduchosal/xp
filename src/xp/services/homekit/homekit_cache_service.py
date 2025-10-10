"""Bubus cache service for caching datapoint responses."""

import logging
from datetime import datetime
from typing import TypedDict, Union

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    LightLevelReceivedEvent,
    OutputStateReceivedEvent,
    ReadDatapointEvent,
    ReadDatapointFromProtocolEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


class CacheEntry(TypedDict):
    """Cache entry type definition."""

    event: Union[OutputStateReceivedEvent, LightLevelReceivedEvent]
    timestamp: datetime


class HomeKitCacheService:
    """
    Cache service that intercepts bubus protocol messages to reduce redundant queries.

    Caches OutputStateReceivedEvent and LightLevelReceivedEvent responses.
    When a ReadDatapointEvent is received, checks cache and either:
    - Returns cached response if available (cache hit)
    - Forwards to protocol via ReadDatapointFromProtocolEvent (cache miss)
    """

    def __init__(self, event_bus: EventBus):
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.cache: dict[tuple[str, DataPointType], CacheEntry] = {}

        # Register event handlers
        # Note: These must be registered BEFORE HomeKitConbusService registers its handlers
        self.event_bus.on(ReadDatapointEvent, self.handle_read_datapoint_event)
        self.event_bus.on(
            OutputStateReceivedEvent, self.handle_output_state_received_event
        )
        self.event_bus.on(
            LightLevelReceivedEvent, self.handle_light_level_received_event
        )

        self.logger.info("HomeKitCacheService initialized")

    def _get_cache_key(
        self, serial_number: str, datapoint_type: DataPointType
    ) -> tuple[str, DataPointType]:
        """Generate cache key from serial number and datapoint type."""
        return (serial_number, datapoint_type)

    def _cache_event(
        self, event: Union[OutputStateReceivedEvent, LightLevelReceivedEvent]
    ) -> None:
        """Store an event in the cache."""
        cache_key = self._get_cache_key(event.serial_number, event.datapoint_type)
        cache_entry: CacheEntry = {
            "event": event,
            "timestamp": datetime.now(),
        }
        self.cache[cache_key] = cache_entry
        self.logger.debug(
            f"Cached event: serial={event.serial_number}, "
            f"type={event.datapoint_type}, value={event.data_value}"
        )

    def _get_cached_event(
        self, serial_number: str, datapoint_type: DataPointType
    ) -> Union[OutputStateReceivedEvent, LightLevelReceivedEvent, None]:
        """Retrieve an event from the cache if it exists."""
        cache_key = self._get_cache_key(serial_number, datapoint_type)
        cache_entry = self.cache.get(cache_key)

        if cache_entry:
            self.logger.debug(
                f"Cache hit: serial={serial_number}, type={datapoint_type}"
            )
            return cache_entry["event"]

        self.logger.debug(f"Cache miss: serial={serial_number}, type={datapoint_type}")
        return None

    def handle_read_datapoint_event(self, event: ReadDatapointEvent) -> None:
        """
        Handle ReadDatapointEvent by checking cache or refresh flag.

        On refresh_cache=True: invalidate cache and force protocol query
        On cache hit: dispatch cached response event
        On cache miss: forward to protocol via ReadDatapointFromProtocolEvent
        """
        self.logger.debug(
            f"Handling ReadDatapointEvent: "
            f"serial={event.serial_number}, "
            f"type={event.datapoint_type}, "
            f"refresh_cache={event.refresh_cache}"
        )

        # Check if cache refresh requested
        if event.refresh_cache:
            self.logger.info(
                f"Cache refresh requested: "
                f"serial={event.serial_number}, "
                f"type={event.datapoint_type}"
            )
            # Invalidate cache entry
            cache_key = self._get_cache_key(event.serial_number, event.datapoint_type)
            if cache_key in self.cache:
                del self.cache[cache_key]
                self.logger.debug(f"Invalidated cache entry: {cache_key}")

        # Normal cache lookup flow
        cached_event = self._get_cached_event(event.serial_number, event.datapoint_type)

        if cached_event:
            # Cache hit - dispatch the cached event
            self.logger.info(
                f"Returning cached response: "
                f"serial={event.serial_number}, "
                f"type={event.datapoint_type}"
            )
            self.event_bus.dispatch(cached_event)
            return

        # Cache miss - forward to protocol
        self.logger.debug(
            f"Forwarding to protocol: "
            f"serial={event.serial_number}, "
            f"type={event.datapoint_type}"
        )
        self.event_bus.dispatch(
            ReadDatapointFromProtocolEvent(
                serial_number=event.serial_number,
                datapoint_type=event.datapoint_type,
            )
        )

    def handle_output_state_received_event(
        self, event: OutputStateReceivedEvent
    ) -> None:
        """Cache OutputStateReceivedEvent for future queries."""
        self.logger.debug(
            f"Caching OutputStateReceivedEvent: serial={event.serial_number}, "
            f"type={event.datapoint_type}, value={event.data_value}"
        )
        self._cache_event(event)

    def handle_light_level_received_event(self, event: LightLevelReceivedEvent) -> None:
        """Cache LightLevelReceivedEvent for future queries."""
        self.logger.debug(
            f"Caching LightLevelReceivedEvent: serial={event.serial_number}, "
            f"type={event.datapoint_type}, value={event.data_value}"
        )
        self._cache_event(event)

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self.logger.info("Clearing cache")
        self.cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "total_entries": len(self.cache),
        }
