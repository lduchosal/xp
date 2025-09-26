"""Cache models for HomeKit cache service.

This module provides cache-related models including cache entries and responses
for the HomeKit caching functionality.
"""

from datetime import datetime
from typing import Any, List, Optional


class CacheEntry:
    """Represents a single cache entry with data, metadata, and expiration.

    Contains the cached data along with timestamp, tags for organization,
    and TTL for expiration management.
    """

    def __init__(self, data: str, tags: List[str], ttl: int = 300):
        """Initialize cache entry.

        Args:
            data: The cached data as string
            tags: List of tags for cache organization and invalidation
            ttl: Time-to-live in seconds (default: 300 seconds / 5 minutes)
        """
        self.data = data
        self.timestamp = datetime.now()
        self.tags = tags
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if cache entry has expired.

        Returns:
            True if the entry is expired based on TTL, False otherwise
        """
        if self.ttl <= 0:
            return False  # Never expires if TTL is 0 or negative

        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl

    def to_dict(self) -> dict:
        """Convert cache entry to dictionary for serialization.

        Returns:
            Dictionary representation of the cache entry
        """
        return {
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create CacheEntry from dictionary.

        Args:
            data: Dictionary containing cache entry data

        Returns:
            CacheEntry instance created from dictionary
        """
        entry = cls(data=data["data"], tags=data["tags"], ttl=data["ttl"])
        entry.timestamp = datetime.fromisoformat(data["timestamp"])
        return entry


class CacheResponse:
    """Response model for cache operations.

    Indicates whether a cache hit or miss occurred along with the data
    and optional error information.
    """

    def __init__(self, data: Any, hit: bool, error: Optional[str] = None):
        """Initialize cache response.

        Args:
            data: The data retrieved (either from cache or fresh)
            hit: True if data was retrieved from cache, False for cache miss
            error: Error message if operation failed
        """
        self.data = data
        self.hit = hit
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert cache response to dictionary.

        Returns:
            Dictionary representation of the cache response
        """
        return {
            "data": self.data,
            "hit": self.hit,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }
