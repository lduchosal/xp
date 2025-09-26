"""Unit tests for cache models."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

from xp.models.cache import CacheEntry, CacheResponse


class TestCacheEntry:
    """Test cases for CacheEntry model"""

    def test_create_cache_entry(self):
        """Test creating a cache entry with default TTL"""
        entry = CacheEntry(data="test_data", tags=["tag1", "tag2"])

        assert entry.data == "test_data"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.ttl == 300  # Default 5 minutes
        assert isinstance(entry.timestamp, datetime)

    def test_create_cache_entry_custom_ttl(self):
        """Test creating a cache entry with custom TTL"""
        entry = CacheEntry(data="test_data", tags=["tag1"], ttl=600)

        assert entry.data == "test_data"
        assert entry.tags == ["tag1"]
        assert entry.ttl == 600

    def test_cache_entry_not_expired_within_ttl(self):
        """Test cache entry is not expired within TTL period"""
        entry = CacheEntry(data="test_data", tags=["tag1"], ttl=300)

        # Should not be expired immediately after creation
        assert not entry.is_expired()

    def test_cache_entry_expired_after_ttl(self):
        """Test cache entry is expired after TTL period"""
        entry = CacheEntry(data="test_data", tags=["tag1"], ttl=1)

        # Mock timestamp to be 2 seconds ago
        past_time = datetime.now() - timedelta(seconds=2)
        with patch.object(entry, "timestamp", past_time):
            assert entry.is_expired()

    def test_cache_entry_never_expires_with_zero_ttl(self):
        """Test cache entry never expires with TTL of 0"""
        entry = CacheEntry(data="test_data", tags=["tag1"], ttl=0)

        # Mock timestamp to be very old
        old_time = datetime.now() - timedelta(hours=24)
        with patch.object(entry, "timestamp", old_time):
            assert not entry.is_expired()

    def test_cache_entry_never_expires_with_negative_ttl(self):
        """Test cache entry never expires with negative TTL"""
        entry = CacheEntry(data="test_data", tags=["tag1"], ttl=-1)

        # Mock timestamp to be very old
        old_time = datetime.now() - timedelta(hours=24)
        with patch.object(entry, "timestamp", old_time):
            assert not entry.is_expired()

    def test_cache_entry_to_dict(self):
        """Test converting cache entry to dictionary"""
        result = CacheEntry(data="test_data", tags=["tag1", "tag2"], ttl=300).to_dict()

        assert result["data"] == "test_data"
        assert result["tags"] == ["tag1", "tag2"]
        assert result["ttl"] == 300
        assert "timestamp" in result
        # Timestamp should be ISO format string
        datetime.fromisoformat(result["timestamp"])

    def test_cache_entry_from_dict(self):
        """Test creating cache entry from dictionary"""
        test_timestamp = datetime.now()
        data = {
            "data": "test_data",
            "tags": ["tag1", "tag2"],
            "ttl": 600,
            "timestamp": test_timestamp.isoformat(),
        }

        entry = CacheEntry.from_dict(data)

        assert entry.data == "test_data"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.ttl == 600
        assert entry.timestamp == test_timestamp

    def test_cache_entry_round_trip_serialization(self):
        """Test cache entry can be serialized and deserialized"""
        original_entry = CacheEntry(data="test_data", tags=["tag1", "tag2"], ttl=600)

        # Convert to dict and back
        data_dict = original_entry.to_dict()
        restored_entry = CacheEntry.from_dict(data_dict)

        assert restored_entry.data == original_entry.data
        assert restored_entry.tags == original_entry.tags
        assert restored_entry.ttl == original_entry.ttl
        assert restored_entry.timestamp == original_entry.timestamp


class TestCacheResponse:
    """Test cases for CacheResponse model"""

    def test_create_cache_response_hit(self):
        """Test creating a cache response for cache hit"""
        response = CacheResponse(data="cached_data", hit=True)

        assert response.data == "cached_data"
        assert response.hit is True
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_create_cache_response_miss(self):
        """Test creating a cache response for cache miss"""
        response = CacheResponse(data="fresh_data", hit=False)

        assert response.data == "fresh_data"
        assert response.hit is False
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_create_cache_response_with_error(self):
        """Test creating a cache response with error"""
        response = CacheResponse(data=None, hit=False, error="Device not found")

        assert response.data is None
        assert response.hit is False
        assert response.error == "Device not found"
        assert isinstance(response.timestamp, datetime)

    def test_cache_response_to_dict(self):
        """Test converting cache response to dictionary"""
        result = CacheResponse(data="test_data", hit=True, error="test_error").to_dict()

        assert result["data"] == "test_data"
        assert result["hit"] is True
        assert result["error"] == "test_error"
        assert "timestamp" in result
        # Timestamp should be ISO format string
        datetime.fromisoformat(result["timestamp"])

    def test_cache_response_to_dict_json_serializable(self):
        """Test cache response dict can be JSON serialized"""
        result = CacheResponse(data="test_data", hit=True).to_dict()

        # Should not raise an exception
        json_str = json.dumps(result)
        assert json_str is not None

        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["data"] == "test_data"
        assert parsed["hit"] is True
