"""Bubus cache service for caching datapoint responses."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, Union

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    LightLevelReceivedEvent,
    OutputStateReceivedEvent,
    ReadDatapointEvent,
    ReadDatapointFromProtocolEvent,
)
from xp.models.telegram.datapoint_type import DataPointType

# Cache file configuration
CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "homekit_cache.json"


class CacheEntry(TypedDict):
    """Cache entry type definition.

    Attributes:
        event: The cached event (OutputStateReceivedEvent or LightLevelReceivedEvent).
        timestamp: When the event was cached.
    """

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

    def __init__(self, event_bus: EventBus, enable_persistence: bool = True):
        """Initialize the HomeKit cache service.

        Args:
            event_bus: Event bus for inter-service communication.
            enable_persistence: Whether to persist cache to disk.
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.cache: dict[tuple[str, DataPointType], CacheEntry] = {}
        self.enable_persistence = enable_persistence

        # Load cache from disk
        if self.enable_persistence:
            self._load_cache()

        # Register event handlers
        # Note: These must be registered BEFORE HomeKitConbusService registers its handlers
        self.event_bus.on(ReadDatapointEvent, self.handle_read_datapoint_event)
        self.event_bus.on(
            OutputStateReceivedEvent, self.handle_output_state_received_event
        )
        self.event_bus.on(
            LightLevelReceivedEvent, self.handle_light_level_received_event
        )

        self.logger.info(
            f"HomeKitCacheService initialized with {len(self.cache)} cached entries"
        )

    def _serialize_cache_key(self, key: tuple[str, DataPointType]) -> str:
        """Serialize cache key to JSON-compatible string."""
        serial_number, datapoint_type = key
        return f"{serial_number}.{datapoint_type.value}"

    def _deserialize_cache_key(self, key_str: str) -> tuple[str, DataPointType]:
        """Deserialize cache key from JSON string."""
        serial_number, datapoint_type_str = key_str.rsplit(".", 1)
        return (serial_number, DataPointType(datapoint_type_str))

    def _serialize_cache(self) -> dict[str, Any]:
        """Serialize cache to JSON-compatible dict."""
        serialized = {}
        for key, entry in self.cache.items():
            key_str = self._serialize_cache_key(key)
            serialized[key_str] = {
                "event": entry["event"].model_dump(mode="json"),
                "timestamp": entry["timestamp"].isoformat(),
            }
        return serialized

    def _deserialize_cache(
        self, data: dict[str, Any]
    ) -> dict[tuple[str, DataPointType], CacheEntry]:
        """Deserialize cache from JSON dict."""
        cache: dict[tuple[str, DataPointType], CacheEntry] = {}
        for key_str, entry_data in data.items():
            try:
                key = self._deserialize_cache_key(key_str)
                event_data = entry_data["event"]

                # Reconstruct event based on datapoint_type
                if key[1] == DataPointType.MODULE_OUTPUT_STATE:
                    event = OutputStateReceivedEvent(**event_data)
                elif key[1] == DataPointType.MODULE_LIGHT_LEVEL:
                    event = LightLevelReceivedEvent(**event_data)
                else:
                    self.logger.warning(f"Unknown datapoint type in cache: {key[1]}")
                    continue

                cache[key] = {
                    "event": event,
                    "timestamp": datetime.fromisoformat(entry_data["timestamp"]),
                }
            except Exception as e:
                self.logger.warning(f"Failed to deserialize cache entry {key_str}: {e}")
                continue

        return cache

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not CACHE_FILE.exists():
            self.logger.debug("No cache file found, starting with empty cache")
            return

        try:
            with CACHE_FILE.open("r") as f:
                data = json.load(f)

            self.cache = self._deserialize_cache(data)
            self.logger.info(f"Loaded {len(self.cache)} entries from cache file")
        except Exception as e:
            self.logger.error(f"Failed to load cache from disk: {e}")
            self.cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk atomically."""
        if not self.enable_persistence:
            return

        try:
            # Ensure cache directory exists
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file, then rename
            temp_file = CACHE_FILE.with_suffix(".tmp")
            with temp_file.open("w") as f:
                json.dump(self._serialize_cache(), f, indent=2)

            # Atomic rename
            temp_file.replace(CACHE_FILE)

            self.logger.debug(f"Saved {len(self.cache)} entries to cache file")
        except Exception as e:
            self.logger.error(f"Failed to save cache to disk: {e}")

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
            f"Cached event: "
            f"serial={event.serial_number}, "
            f"type={event.datapoint_type}, "
            f"value={event.data_value}"
        )

        # Persist to disk
        self._save_cache()

    def _get_cached_event(
        self, serial_number: str, datapoint_type: DataPointType
    ) -> Union[OutputStateReceivedEvent, LightLevelReceivedEvent, None]:
        """Retrieve an event from the cache if it exists."""
        cache_key = self._get_cache_key(serial_number, datapoint_type)
        cache_entry = self.cache.get(cache_key)

        if cache_entry:
            self.logger.debug(
                f"Cache hit: " f"serial={serial_number}, " f"type={datapoint_type}"
            )
            return cache_entry["event"]

        self.logger.debug(f"Cache miss: serial={serial_number}, type={datapoint_type}")
        return None

    def handle_read_datapoint_event(self, event: ReadDatapointEvent) -> None:
        """Handle ReadDatapointEvent by checking cache or refresh flag.

        On refresh_cache=True: invalidate cache and force protocol query
        On cache hit: dispatch cached response event
        On cache miss: forward to protocol via ReadDatapointFromProtocolEvent

        Args:
            event: Read datapoint event with serial number, datapoint type, and refresh flag.
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
                # Persist invalidation
                self._save_cache()

        # Normal cache lookup flow
        cached_event = self._get_cached_event(event.serial_number, event.datapoint_type)

        if cached_event:
            # Cache hit - dispatch the cached event
            self.logger.debug(
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
        """Cache OutputStateReceivedEvent for future queries.

        Args:
            event: Output state received event to cache.
        """
        self.logger.debug(
            f"Caching OutputStateReceivedEvent: "
            f"serial={event.serial_number}, "
            f"type={event.datapoint_type}, "
            f"value={event.data_value}"
        )
        self._cache_event(event)

    def handle_light_level_received_event(self, event: LightLevelReceivedEvent) -> None:
        """Cache LightLevelReceivedEvent for future queries.

        Args:
            event: Light level received event to cache.
        """
        self.logger.debug(
            f"Caching LightLevelReceivedEvent: "
            f"serial={event.serial_number}, "
            f"type={event.datapoint_type}, "
            f"value={event.data_value}"
        )
        self._cache_event(event)

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self.logger.info("Clearing cache")
        self.cache.clear()
        self._save_cache()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics including total_entries.
        """
        return {
            "total_entries": len(self.cache),
        }
