"""HomeKit Cache Service for intelligent caching of Conson module data.

This service provides caching functionality for frequently accessed ConBus
output states with TTL expiration, event-based invalidation, and file persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from . import TelegramService, TelegramParsingError
from .conbus_lightlevel_service import ConbusLightlevelService
from .conbus_output_service import ConbusOutputService
from ..models.action_type import ActionType
from ..models.cache import CacheEntry, CacheResponse


class HomeKitCacheService:
    """Intelligent caching service for HomeKit device states.

    Provides caching of expensive ConBus module queries with TTL expiration,
    event-based invalidation, and persistent storage for faster startup times.
    """

    def __init__(
        self, config_path: str = "cli.yml", cache_file: str = ".homekit_cache.json"
    ):
        """Initialize the HomeKit cache service.

        Args:
            config_path: Path to configuration file for ConBus service
            cache_file: Custom cache file path (defaults to ~/.homekit_cache.json)
        """
        self.logger = logging.getLogger(__name__)
        self.conbus_output_service = ConbusOutputService(config_path)
        self.conbus_lightlevel_service = ConbusLightlevelService(config_path)
        self.telegram_service = TelegramService()
        self.cache_file = Path(cache_file)

        # In-memory cache storage
        self.cache: Dict[str, CacheEntry] = {}

        # Load existing cache from file
        self._load_cache()

    def get(self, key: str, tag: str) -> CacheResponse:
        """Retrieve data from cache or fetch from device.

        Args:
            key: Cache key (typically device serial number)
            tag: Tag for cache organization

        Returns:
            CacheResponse with data and hit/miss status
        """
        cache_key = key

        # Check if key exists in cache and is not expired
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return CacheResponse(data=entry.data, hit=True)
            else:
                # Remove expired entry
                self.logger.debug(f"Cache expired for key: {cache_key}")
                del self.cache[cache_key]
                self._save_cache()

        # Cache miss - query device
        self.logger.debug(f"Cache miss for key: {cache_key}, querying device")
        try:
            response = self.conbus_output_service.get_output_state(key)

            if (
                response.success
                and response.datapoint_telegram
                and response.datapoint_telegram.raw_telegram
            ):
                data = response.datapoint_telegram.raw_telegram
                # Store in cache
                self.cache[cache_key] = CacheEntry(
                    data=data, tags=[tag], ttl=300  # 5 minutes default TTL
                )
                self._save_cache()

                return CacheResponse(data=data, hit=False)
            else:
                error_msg = f"Failed to query device {key}: {response.error}"
                self.logger.error(error_msg)
                return CacheResponse(data=None, hit=False, error=error_msg)

        except Exception as e:
            error_msg = f"Error querying device {key}: {e}"
            self.logger.error(error_msg)
            return CacheResponse(data=None, hit=False, error=error_msg)

    def set(self, key: str, tag: str, data: str) -> None:
        """Manually set cache entry.

        Args:
            key: Cache key
            tag: Tag for cache organization
            data: Data to cache
        """
        cache_key = key

        # Update existing entry or create new one
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            entry.data = data
            entry.timestamp = datetime.now()
            if tag not in entry.tags:
                entry.tags.append(tag)
        else:
            self.cache[cache_key] = CacheEntry(data=data, tags=[tag])

        self._save_cache()
        self.logger.debug(f"Cache entry set for key: {cache_key}")

    def clear(self, key_or_tag: Optional[str] = None) -> None:
        """Clear cache entries by key or tag.

        Args:
            key_or_tag: Specific key to clear or tag to clear all entries with that tag.
                       If None, clears entire cache.
        """
        if key_or_tag is None:
            # Clear entire cache
            self.cache.clear()
            self.logger.info("Entire cache cleared")
        elif key_or_tag in self.cache:
            # Clear specific key
            del self.cache[key_or_tag]
            self.logger.debug(f"Cache entry cleared for key: {key_or_tag}")
        else:
            # Clear by tag
            keys_to_remove = [
                cache_key
                for cache_key, entry in self.cache.items()
                if key_or_tag in entry.tags
            ]

            for cache_key in keys_to_remove:
                del self.cache[cache_key]

            self.logger.debug(
                f"Cache entries cleared for tag: {key_or_tag} ({len(keys_to_remove)} entries)"
            )

        self._save_cache()

    def items(self) -> Dict[str, str]:
        """Get all cached items.

        Returns:
            Dictionary mapping cache keys to their data values
        """
        # Remove expired entries first
        expired_keys = [
            cache_key for cache_key, entry in self.cache.items() if entry.is_expired()
        ]

        for cache_key in expired_keys:
            del self.cache[cache_key]

        if expired_keys:
            self._save_cache()

        return {key: entry.data for key, entry in self.cache.items()}

    def received_event(self, event: str) -> None:
        """Handle received event for cache invalidation.

        Args:
            event: Event name to invalidate cache entries for
        """
        keys_to_remove = [
            cache_key for cache_key, entry in self.cache.items() if event in entry.tags
        ]

        for cache_key in keys_to_remove:
            del self.cache[cache_key]

        if keys_to_remove:
            self._save_cache()
            self.logger.debug(
                f"Cache invalidated for event: {event} ({len(keys_to_remove)} entries)"
            )

    def _load_cache(self) -> None:
        """Load cache from persistent storage."""
        try:
            if self.cache_file.exists():
                with Path(self.cache_file).open("r") as f:
                    cache_data = json.load(f)

                # Convert dictionary back to CacheEntry objects
                for key, entry_data in cache_data.items():
                    try:
                        self.cache[key] = CacheEntry.from_dict(entry_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to load cache entry {key}: {e}")

                self.logger.debug(
                    f"Loaded {len(self.cache)} cache entries from {self.cache_file}"
                )

        except Exception as e:
            self.logger.error(f"Failed to load cache from {self.cache_file}: {e}")
            self.cache = {}

    def _save_cache(self) -> None:
        """Save cache to persistent storage."""
        try:
            # Ensure cache directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert CacheEntry objects to dictionaries
            cache_data = {}
            for key, entry in self.cache.items():
                cache_data[key] = entry.to_dict()

            # Write to file
            with Path(self.cache_file).open("w") as f:
                json.dump(cache_data, f, indent=2)

            self.logger.debug(
                f"Saved {len(self.cache)} cache entries to {self.cache_file}"
            )

        except Exception as e:
            self.logger.error(f"Failed to save cache to {self.cache_file}: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
        }

    def send_action(
        self, serial_number: str, output_number: int, action_type: ActionType
    ) -> None:

        conbus_response = self.conbus_output_service.send_action(
            serial_number, output_number, action_type
        )
        if not conbus_response.success or conbus_response.received_telegrams is None:
            self.logger.error(f"Action failed or no response: {conbus_response}")
            return

        for raw_telegram in conbus_response.received_telegrams:
            try:
                telegram = self.telegram_service.parse_event_telegram(raw_telegram)
                self.received_event(telegram.raw_telegram)
            except TelegramParsingError as e:
                self.logger.info(f"Not an event telegram {raw_telegram}: {e}")

    def get_brightness(self, serial_number: str, output_number: int) -> int:
        lightlevel_response = self.conbus_lightlevel_service.get_lightlevel(
            serial_number, output_number
        )
        if not lightlevel_response.success or not lightlevel_response.level:
            return 0
        return lightlevel_response.level

    def set_brightness(
        self, serial_number: str, output_number: int, value: int
    ) -> None:
        self.conbus_lightlevel_service.set_lightlevel(
            serial_number, output_number, value
        )
