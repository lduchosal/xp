"""Unit tests for TelegramDebounceService"""

import asyncio
from unittest.mock import AsyncMock, Mock, call

import pytest
from bubus import EventBus

from xp.models.protocol.conbus_protocol import ReadDatapointFromProtocolEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.protocol.telegram_debounce_service import TelegramDebounceService
from xp.services.protocol.telegram_protocol import TelegramProtocol


class TestTelegramDebounceService:
    """Test cases for TelegramDebounceService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.telegram_protocol.sendFrame = Mock()
        self.service = TelegramDebounceService(
            self.event_bus,
            self.telegram_protocol,
            debounce_ms=50,
        )

    def test_init(self):
        """Test service initialization"""
        event_bus = Mock(spec=EventBus)
        telegram_protocol = Mock(spec=TelegramProtocol)

        service = TelegramDebounceService(
            event_bus,
            telegram_protocol,
            debounce_ms=100,
        )

        assert service.event_bus == event_bus
        assert service.telegram_protocol == telegram_protocol
        assert service.debounce_ms == 100
        assert service.logger is not None
        assert service.request_queue == {}
        assert service.timer_handle is None

        # Verify event handler is registered
        event_bus.on.assert_called_once_with(
            ReadDatapointFromProtocolEvent,
            service.handle_read_datapoint_request
        )

    def test_create_dedup_key_format(self):
        """Test dedup key format is serial:datapoint_value"""
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        dedup_key = self.service._create_dedup_key(event)

        assert dedup_key == "012345678901:12"

    def test_create_dedup_key_different_datapoints(self):
        """Test different datapoint types create different keys"""
        event1 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event2 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
        )

        key1 = self.service._create_dedup_key(event1)
        key2 = self.service._create_dedup_key(event2)

        assert key1 == "012345678901:12"
        assert key2 == "012345678901:15"
        assert key1 != key2

    def test_create_dedup_key_different_serials(self):
        """Test different serial numbers create different keys"""
        event1 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event2 = ReadDatapointFromProtocolEvent(
            serial_number="987654321098",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        key1 = self.service._create_dedup_key(event1)
        key2 = self.service._create_dedup_key(event2)

        assert key1 == "012345678901:12"
        assert key2 == "987654321098:12"
        assert key1 != key2

    def test_handle_request_queues_event(self):
        """Test that handling request queues the event"""
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_request(event)

        # Check event is queued
        dedup_key = "012345678901:12"
        assert dedup_key in self.service.request_queue
        assert len(self.service.request_queue[dedup_key]) == 1
        assert self.service.request_queue[dedup_key][0] == event

    def test_handle_request_timer_set(self):
        """Test that handling request sets debounce timer"""
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_request(event)

        # Timer should be set
        assert self.service.timer_handle is not None

    def test_handle_multiple_identical_requests_queued_together(self):
        """Test that multiple identical requests are queued under same key"""
        event1 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event2 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event3 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event4 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_request(event1)
        self.service.handle_read_datapoint_request(event2)
        self.service.handle_read_datapoint_request(event3)
        self.service.handle_read_datapoint_request(event4)

        # All 4 should be in same queue
        dedup_key = "012345678901:12"
        assert len(self.service.request_queue) == 1  # Only one unique key
        assert len(self.service.request_queue[dedup_key]) == 4  # 4 events queued

    def test_handle_different_requests_separate_queues(self):
        """Test that different requests use separate queue entries"""
        event1 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event2 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
        )
        event3 = ReadDatapointFromProtocolEvent(
            serial_number="987654321098",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.handle_read_datapoint_request(event1)
        self.service.handle_read_datapoint_request(event2)
        self.service.handle_read_datapoint_request(event3)

        # Should have 3 separate queue entries
        assert len(self.service.request_queue) == 3
        assert "012345678901:12" in self.service.request_queue
        assert "012345678901:15" in self.service.request_queue
        assert "987654321098:12" in self.service.request_queue

    @pytest.mark.asyncio
    async def test_process_queue_sends_unique_telegrams(self):
        """Test that process_queue sends one telegram per unique request"""
        # Queue 4 identical requests
        for _ in range(4):
            event = ReadDatapointFromProtocolEvent(
                serial_number="012345678901",
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            )
            self.service.request_queue.setdefault("012345678901:12", []).append(event)

        await self.service._process_queue()

        # Should send telegram only ONCE
        self.telegram_protocol.sendFrame.assert_called_once_with(
            b"S012345678901F02D12"
        )

    @pytest.mark.asyncio
    async def test_process_queue_sends_all_unique_telegrams(self):
        """Test that process_queue sends all unique telegrams"""
        # Queue different requests
        event1 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event2 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
        )
        event3 = ReadDatapointFromProtocolEvent(
            serial_number="987654321098",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        self.service.request_queue["012345678901:12"] = [event1]
        self.service.request_queue["012345678901:15"] = [event2]
        self.service.request_queue["987654321098:12"] = [event3]

        await self.service._process_queue()

        # Should send 3 different telegrams
        assert self.telegram_protocol.sendFrame.call_count == 3
        self.telegram_protocol.sendFrame.assert_any_call(b"S012345678901F02D12")
        self.telegram_protocol.sendFrame.assert_any_call(b"S012345678901F02D15")
        self.telegram_protocol.sendFrame.assert_any_call(b"S987654321098F02D12")

    @pytest.mark.asyncio
    async def test_process_queue_clears_queue(self):
        """Test that process_queue clears the request queue"""
        # Queue some requests
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        self.service.request_queue["012345678901:12"] = [event]

        await self.service._process_queue()

        # Queue should be empty
        assert len(self.service.request_queue) == 0

    @pytest.mark.asyncio
    async def test_process_queue_clears_timer_handle(self):
        """Test that process_queue clears timer handle"""
        # Set up queue and timer
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        self.service.request_queue["012345678901:12"] = [event]
        self.service.timer_handle = Mock()

        await self.service._process_queue()

        # Timer handle should be None
        assert self.service.timer_handle is None

    @pytest.mark.asyncio
    async def test_process_empty_queue_does_nothing(self):
        """Test that processing empty queue is safe"""
        # Empty queue
        self.service.request_queue = {}

        await self.service._process_queue()

        # Should not send any telegrams
        self.telegram_protocol.sendFrame.assert_not_called()

    @pytest.mark.asyncio
    async def test_deduplication_statistics_logged(self):
        """Test that deduplication statistics are calculated correctly"""
        # Queue 4 identical + 1 unique = 5 total, 2 unique
        for _ in range(4):
            event = ReadDatapointFromProtocolEvent(
                serial_number="012345678901",
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            )
            self.service.request_queue.setdefault("012345678901:12", []).append(event)

        event2 = ReadDatapointFromProtocolEvent(
            serial_number="987654321098",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        self.service.request_queue["987654321098:12"] = [event2]

        await self.service._process_queue()

        # Should have sent 2 unique telegrams (4 + 1 = 5 total, 3 deduped)
        assert self.telegram_protocol.sendFrame.call_count == 2

    @pytest.mark.asyncio
    async def test_telegram_format_output_state(self):
        """Test telegram format for OUTPUT_STATE datapoint"""
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        self.service.request_queue["012345678901:12"] = [event]

        await self.service._process_queue()

        # Telegram format: S{serial}F{function}D{datapoint}
        # F02 = READ_DATAPOINT, D12 = OUTPUT_STATE
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D12")

    @pytest.mark.asyncio
    async def test_telegram_format_light_level(self):
        """Test telegram format for LIGHT_LEVEL datapoint"""
        event = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
        )
        self.service.request_queue["012345678901:15"] = [event]

        await self.service._process_queue()

        # Telegram format: S{serial}F{function}D{datapoint}
        # F02 = READ_DATAPOINT, D15 = LIGHT_LEVEL
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D15")

    def test_timer_reset_on_new_request(self):
        """Test that timer is reset when new request arrives"""
        event1 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )
        event2 = ReadDatapointFromProtocolEvent(
            serial_number="012345678901",
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        # First request sets timer
        self.service.handle_read_datapoint_request(event1)
        first_timer = self.service.timer_handle

        # Second request should cancel and reset timer
        self.service.handle_read_datapoint_request(event2)
        second_timer = self.service.timer_handle

        # Timer should be reset (different handle)
        assert first_timer is not None
        assert second_timer is not None
        # First timer should have been cancelled
        assert first_timer.cancelled()

    @pytest.mark.asyncio
    async def test_uses_first_event_in_duplicate_list(self):
        """Test that processing uses the first event from duplicate list"""
        # Create 4 identical events
        events = [
            ReadDatapointFromProtocolEvent(
                serial_number="012345678901",
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            )
            for _ in range(4)
        ]

        self.service.request_queue["012345678901:12"] = events

        await self.service._process_queue()

        # Should use first event (they're all identical anyway)
        # Verify telegram was sent with correct format
        self.telegram_protocol.sendFrame.assert_called_once_with(
            b"S012345678901F02D12"
        )
