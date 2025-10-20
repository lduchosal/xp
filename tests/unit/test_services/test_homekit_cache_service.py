"""Unit tests for HomeKitCacheService."""

from unittest.mock import Mock

from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    LightLevelReceivedEvent,
    OutputStateReceivedEvent,
    ReadDatapointEvent,
    ReadDatapointFromProtocolEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.homekit.homekit_cache_service import HomeKitCacheService


class TestHomeKitCacheService:
    """Test cases for HomeKitCacheService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.service = HomeKitCacheService(self.event_bus, enable_persistence=False)

    def test_init(self):
        """Test service initialization."""
        event_bus = Mock(spec=EventBus)
        service = HomeKitCacheService(event_bus, enable_persistence=False)

        assert service.event_bus == event_bus
        assert service.logger is not None
        assert service.cache == {}

        # Verify event handlers are registered
        assert event_bus.on.call_count == 3
        event_bus.on.assert_any_call(
            ReadDatapointEvent, service.handle_read_datapoint_event
        )
        event_bus.on.assert_any_call(
            OutputStateReceivedEvent, service.handle_output_state_received_event
        )
        event_bus.on.assert_any_call(
            LightLevelReceivedEvent, service.handle_light_level_received_event
        )

    def test_cache_output_state_received_event(self):
        """Test caching OutputStateReceivedEvent."""
        event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )

        self.service.handle_output_state_received_event(event)

        # Verify event is cached
        cache_key = ("1234567890", DataPointType.MODULE_OUTPUT_STATE)
        assert cache_key in self.service.cache
        assert self.service.cache[cache_key]["event"] == event
        assert "timestamp" in self.service.cache[cache_key]

    def test_cache_light_level_received_event(self):
        """Test caching LightLevelReceivedEvent."""
        event = LightLevelReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="02:075",
        )

        self.service.handle_light_level_received_event(event)

        # Verify event is cached
        cache_key = ("1234567890", DataPointType.MODULE_LIGHT_LEVEL)
        assert cache_key in self.service.cache
        assert self.service.cache[cache_key]["event"] == event

    def test_read_datapoint_cache_miss_forwards_to_protocol(self):
        """Test ReadDatapointEvent with cache miss forwards to protocol."""
        event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_event(event)

        # Should dispatch ReadDatapointFromProtocolEvent
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointFromProtocolEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_read_datapoint_cache_hit_returns_cached(self):
        """Test ReadDatapointEvent with cache hit returns cached event."""
        # First, cache an event
        cached_event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        self.service.handle_output_state_received_event(cached_event)

        # Reset mock to clear previous calls
        self.event_bus.dispatch.reset_mock()

        # Now query the same datapoint
        query_event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_event(query_event)

        # Should dispatch the cached event, NOT ReadDatapointFromProtocolEvent
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, OutputStateReceivedEvent)
        assert dispatched_event == cached_event
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.data_value == "01:1"

    def test_cache_key_uniqueness_by_serial_number(self):
        """Test that different serial numbers have separate cache entries."""
        event1 = OutputStateReceivedEvent(
            serial_number="1111111111",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        event2 = OutputStateReceivedEvent(
            serial_number="2222222222",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:0",
        )

        self.service.handle_output_state_received_event(event1)
        self.service.handle_output_state_received_event(event2)

        # Both should be cached separately
        assert len(self.service.cache) == 2
        cache_key1 = ("1111111111", DataPointType.MODULE_OUTPUT_STATE)
        cache_key2 = ("2222222222", DataPointType.MODULE_OUTPUT_STATE)
        assert self.service.cache[cache_key1]["event"] == event1
        assert self.service.cache[cache_key2]["event"] == event2

    def test_cache_key_uniqueness_by_datapoint_type(self):
        """Test that different datapoint types have separate cache entries."""
        event1 = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        event2 = LightLevelReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="02:050",
        )

        self.service.handle_output_state_received_event(event1)
        self.service.handle_light_level_received_event(event2)

        # Both should be cached separately for same serial number
        assert len(self.service.cache) == 2
        cache_key1 = ("1234567890", DataPointType.MODULE_OUTPUT_STATE)
        cache_key2 = ("1234567890", DataPointType.MODULE_LIGHT_LEVEL)
        assert self.service.cache[cache_key1]["event"] == event1
        assert self.service.cache[cache_key2]["event"] == event2

    def test_cache_overwrite_on_duplicate(self):
        """Test that caching the same key twice overwrites the previous value."""
        event1 = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:0",
        )
        event2 = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )

        self.service.handle_output_state_received_event(event1)
        self.service.handle_output_state_received_event(event2)

        # Should only have one entry, with the latest value
        assert len(self.service.cache) == 1
        cache_key = ("1234567890", DataPointType.MODULE_OUTPUT_STATE)
        cached_event = self.service.cache[cache_key]["event"]
        assert cached_event == event2
        assert cached_event.data_value == "01:1"

    def test_clear_cache(self):
        """Test clearing the cache."""
        # Add some events
        event1 = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        event2 = LightLevelReceivedEvent(
            serial_number="9876543210",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="02:100",
        )

        self.service.handle_output_state_received_event(event1)
        self.service.handle_light_level_received_event(event2)

        assert len(self.service.cache) == 2

        # Clear the cache
        self.service.clear_cache()

        assert len(self.service.cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Initially empty
        stats = self.service.get_cache_stats()
        assert stats["total_entries"] == 0

        # Add some events
        event1 = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        event2 = LightLevelReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="02:050",
        )

        self.service.handle_output_state_received_event(event1)
        self.service.handle_light_level_received_event(event2)

        stats = self.service.get_cache_stats()
        assert stats["total_entries"] == 2

    def test_read_datapoint_different_serial_cache_miss(self):
        """Test that querying different serial number results in cache miss."""
        # Cache event for serial 1111111111
        cached_event = OutputStateReceivedEvent(
            serial_number="1111111111",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        self.service.handle_output_state_received_event(cached_event)

        # Query for serial 2222222222
        query_event = ReadDatapointEvent(
            serial_number="2222222222",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_event(query_event)

        # Should forward to protocol
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointFromProtocolEvent)
        assert dispatched_event.serial_number == "2222222222"

    def test_read_datapoint_different_type_cache_miss(self):
        """Test that querying different datapoint type results in cache miss."""
        # Cache OUTPUT_STATE
        cached_event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        self.service.handle_output_state_received_event(cached_event)

        # Query for LIGHT_LEVEL
        query_event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
        )

        self.service.handle_read_datapoint_event(query_event)

        # Should forward to protocol
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointFromProtocolEvent)
        assert dispatched_event.datapoint_type == DataPointType.MODULE_LIGHT_LEVEL

    def test_refresh_cache_invalidates_cache_entry(self):
        """Test that refresh_cache=True invalidates cache and forces protocol query."""
        # First, cache an event
        cached_event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        self.service.handle_output_state_received_event(cached_event)

        # Verify event is cached
        cache_key = ("1234567890", DataPointType.MODULE_OUTPUT_STATE)
        assert cache_key in self.service.cache

        # Reset mock to clear previous calls
        self.event_bus.dispatch.reset_mock()

        # Now request refresh_cache=True
        refresh_event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            refresh_cache=True,
        )

        self.service.handle_read_datapoint_event(refresh_event)

        # Cache entry should be invalidated
        assert cache_key not in self.service.cache

        # Should dispatch ReadDatapointFromProtocolEvent (force fresh query)
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointFromProtocolEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_refresh_cache_without_existing_cache_forces_query(self):
        """Test that refresh_cache=True works even when no cache entry exists."""
        # No cached event

        # Request refresh_cache=True
        refresh_event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            refresh_cache=True,
        )

        self.service.handle_read_datapoint_event(refresh_event)

        # Should dispatch ReadDatapointFromProtocolEvent
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, ReadDatapointFromProtocolEvent)
        assert dispatched_event.serial_number == "1234567890"
        assert dispatched_event.datapoint_type == DataPointType.MODULE_OUTPUT_STATE

    def test_refresh_cache_false_uses_normal_cache_logic(self):
        """Test that refresh_cache=False uses normal cache hit/miss logic."""
        # Cache an event
        cached_event = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        self.service.handle_output_state_received_event(cached_event)

        # Reset mock
        self.event_bus.dispatch.reset_mock()

        # Query with refresh_cache=False (default)
        query_event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            refresh_cache=False,
        )

        self.service.handle_read_datapoint_event(query_event)

        # Should return cached event (cache hit)
        self.event_bus.dispatch.assert_called_once()
        dispatched_event = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, OutputStateReceivedEvent)
        assert dispatched_event == cached_event

    def test_refresh_cache_only_invalidates_specified_entry(self):
        """Test that refresh_cache only invalidates the specified cache entry."""
        # Cache multiple events
        event1 = OutputStateReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:1",
        )
        event2 = LightLevelReceivedEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value="02:050",
        )
        event3 = OutputStateReceivedEvent(
            serial_number="9876543210",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            data_value="01:0",
        )

        self.service.handle_output_state_received_event(event1)
        self.service.handle_light_level_received_event(event2)
        self.service.handle_output_state_received_event(event3)

        # Verify all three are cached
        assert len(self.service.cache) == 3

        # Refresh only event1
        refresh_event = ReadDatapointEvent(
            serial_number="1234567890",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            refresh_cache=True,
        )

        self.service.handle_read_datapoint_event(refresh_event)

        # Only event1 should be invalidated, event2 and event3 should remain
        assert len(self.service.cache) == 2
        cache_key1 = ("1234567890", DataPointType.MODULE_OUTPUT_STATE)
        cache_key2 = ("1234567890", DataPointType.MODULE_LIGHT_LEVEL)
        cache_key3 = ("9876543210", DataPointType.MODULE_OUTPUT_STATE)

        assert cache_key1 not in self.service.cache
        assert cache_key2 in self.service.cache
        assert cache_key3 in self.service.cache
