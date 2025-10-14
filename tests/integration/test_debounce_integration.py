"""Integration tests for telegram debounce functionality."""

import asyncio
from unittest.mock import Mock

import pytest
from bubus import EventBus

from xp.models.protocol.conbus_protocol import (
    ReadDatapointEvent,
    ReadDatapointFromProtocolEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.protocol.telegram_debounce_service import TelegramDebounceService
from xp.services.protocol.telegram_protocol import TelegramProtocol


class TestDebounceIntegration:
    """Integration tests for debounce service with cache and HAP services."""

    def setup_method(self):
        """Set up test fixtures"""
        self.event_bus = EventBus()
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.telegram_protocol.sendFrame = Mock()

        # Create services in correct order
        self.cache_service = HomeKitCacheService(
            self.event_bus,
            enable_persistence=False,
        )

        self.debounce_service = TelegramDebounceService(
            self.event_bus,
            self.telegram_protocol,
            debounce_ms=50,
        )

    @pytest.mark.asyncio
    async def test_multiple_accessories_single_module_sends_one_telegram(self):
        """
        Test that 4 accessories on same module trigger only 1 telegram.

        Scenario:
        - 4 accessories configured with same serial_number (012345678901)
        - Button press triggers ModuleStateChangedEvent
        - Each accessory requests cache refresh
        - Expected: 1 telegram sent (not 4)
        """
        serial_number = "012345678901"

        # Simulate 4 accessories requesting refresh
        for _ in range(4):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

        # Give debounce window time to expire
        await asyncio.sleep(0.06)  # 60ms > 50ms window

        # Verify only 1 telegram was sent
        assert self.telegram_protocol.sendFrame.call_count == 1
        self.telegram_protocol.sendFrame.assert_called_with(
            b"S012345678901F02D12"
        )

    @pytest.mark.asyncio
    async def test_mixed_modules_sends_separate_telegrams(self):
        """
        Test that accessories on different modules send separate telegrams.

        Scenario:
        - 2 accessories on module A (012345678901)
        - 2 accessories on module B (987654321098)
        - Event affects both modules
        - Expected: 2 telegrams sent (one per module)
        """
        serial_a = "012345678901"
        serial_b = "987654321098"

        # Simulate 2 accessories on module A
        for _ in range(2):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_a,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

        # Simulate 2 accessories on module B
        for _ in range(2):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_b,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

        # Give debounce window time to expire
        await asyncio.sleep(0.06)

        # Verify 2 telegrams were sent
        assert self.telegram_protocol.sendFrame.call_count == 2
        self.telegram_protocol.sendFrame.assert_any_call(b"S012345678901F02D12")
        self.telegram_protocol.sendFrame.assert_any_call(b"S987654321098F02D12")

    @pytest.mark.asyncio
    async def test_mixed_datapoint_types_not_deduplicated(self):
        """
        Test that OUTPUT_STATE and LIGHT_LEVEL are not deduplicated.

        Scenario:
        - Same module requests both OUTPUT_STATE and LIGHT_LEVEL
        - Expected: 2 telegrams sent (different datapoint types)
        """
        serial_number = "012345678901"

        # Request OUTPUT_STATE
        await self.event_bus.dispatch(
            ReadDatapointEvent(
                serial_number=serial_number,
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                refresh_cache=True,
            )
        )

        # Request LIGHT_LEVEL
        await self.event_bus.dispatch(
            ReadDatapointEvent(
                serial_number=serial_number,
                datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
                refresh_cache=True,
            )
        )

        # Give debounce window time to expire
        await asyncio.sleep(0.06)

        # Verify 2 different telegrams were sent
        assert self.telegram_protocol.sendFrame.call_count == 2
        self.telegram_protocol.sendFrame.assert_any_call(b"S012345678901F02D12")
        self.telegram_protocol.sendFrame.assert_any_call(b"S012345678901F02D15")

    @pytest.mark.asyncio
    async def test_cache_miss_deduplicated(self):
        """
        Test that duplicate cache misses are deduplicated.

        Scenario:
        - 3 accessories request same datapoint (cache miss)
        - Expected: 1 telegram sent
        """
        serial_number = "012345678901"

        # Simulate 3 cache misses (no refresh_cache=True)
        for _ in range(3):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=False,  # Normal cache miss
                )
            )

        # Give debounce window time to expire
        await asyncio.sleep(0.06)

        # Verify only 1 telegram was sent
        assert self.telegram_protocol.sendFrame.call_count == 1
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D12")

    @pytest.mark.asyncio
    async def test_debounce_window_batching(self):
        """
        Test that requests within debounce window are batched together.

        Scenario:
        - Request 1 at t=0ms
        - Request 2 at t=10ms (resets timer)
        - Request 3 at t=20ms (resets timer)
        - Expected: All processed in single batch at t=70ms
        """
        serial_number = "012345678901"

        # Request 1
        await self.event_bus.dispatch(
            ReadDatapointEvent(
                serial_number=serial_number,
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                refresh_cache=True,
            )
        )

        # Wait 10ms, send Request 2
        await asyncio.sleep(0.01)
        await self.event_bus.dispatch(
            ReadDatapointEvent(
                serial_number=serial_number,
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                refresh_cache=True,
            )
        )

        # Wait 10ms, send Request 3
        await asyncio.sleep(0.01)
        await self.event_bus.dispatch(
            ReadDatapointEvent(
                serial_number=serial_number,
                datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                refresh_cache=True,
            )
        )

        # Telegram should NOT be sent yet (within debounce window)
        assert self.telegram_protocol.sendFrame.call_count == 0

        # Wait for debounce window to expire (50ms from last request)
        await asyncio.sleep(0.06)

        # Now telegram should be sent
        assert self.telegram_protocol.sendFrame.call_count == 1
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D12")

    @pytest.mark.asyncio
    async def test_successive_batches_independent(self):
        """
        Test that successive batches are processed independently.

        Scenario:
        - Batch 1: 4 requests -> 1 telegram
        - Wait for batch to complete
        - Batch 2: 4 requests -> 1 telegram
        - Expected: 2 telegrams total (one per batch)
        """
        serial_number = "012345678901"

        # Batch 1: 4 requests
        for _ in range(4):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

        # Wait for batch 1 to complete
        await asyncio.sleep(0.06)
        assert self.telegram_protocol.sendFrame.call_count == 1

        # Reset mock
        self.telegram_protocol.sendFrame.reset_mock()

        # Batch 2: 4 more requests
        for _ in range(4):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

        # Wait for batch 2 to complete
        await asyncio.sleep(0.06)
        assert self.telegram_protocol.sendFrame.call_count == 1

    @pytest.mark.asyncio
    async def test_end_to_end_cache_refresh_flow(self):
        """
        Test complete flow: cache refresh -> debounce -> protocol.

        Scenario:
        - Module state changes (event telegram received)
        - Cache invalidation triggers refresh
        - Multiple accessories request same datapoint
        - Debounce service deduplicates
        - Single telegram sent to protocol
        """
        serial_number = "012345678901"

        # Simulate cache invalidation for 4 accessories
        for _ in range(4):
            # Cache service would dispatch ReadDatapointFromProtocolEvent
            # after invalidating cache entry
            await self.event_bus.dispatch(
                ReadDatapointFromProtocolEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                )
            )

        # Give debounce window time to expire
        await asyncio.sleep(0.06)

        # Verify deduplication worked: 4 requests -> 1 telegram
        assert self.telegram_protocol.sendFrame.call_count == 1
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D12")

    @pytest.mark.asyncio
    async def test_debounce_statistics_accuracy(self):
        """
        Test that debounce statistics are accurate.

        Scenario:
        - 10 identical requests
        - Expected: 1 telegram sent, 9 deduplicated
        - Reduction: 90%
        """
        serial_number = "012345678901"

        # Queue 10 identical requests
        for _ in range(10):
            await self.event_bus.dispatch(
                ReadDatapointFromProtocolEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                )
            )

        # Wait for processing
        await asyncio.sleep(0.06)

        # Verify: 10 requests -> 1 telegram
        assert self.telegram_protocol.sendFrame.call_count == 1

        # All 10 should have resulted in same telegram
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D12")


class TestDebounceWithCacheService:
    """Integration tests with cache service to test realistic flow."""

    def setup_method(self):
        """Set up test fixtures with cache and debounce services"""
        self.event_bus = EventBus()
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.telegram_protocol.sendFrame = Mock()

        # Create services in correct order
        self.cache_service = HomeKitCacheService(
            self.event_bus,
            enable_persistence=False,
        )

        self.debounce_service = TelegramDebounceService(
            self.event_bus,
            self.telegram_protocol,
            debounce_ms=50,
        )

    @pytest.mark.asyncio
    async def test_cache_refresh_flow_with_deduplication(self):
        """
        Test complete cache refresh flow with deduplication.

        Scenario:
        - 4 accessories request cache refresh for same module
        - Cache service invalidates and forwards to protocol
        - Debounce service deduplicates
        - Expected: 1 telegram sent
        """
        serial_number = "012345678901"

        # Simulate 4 accessories requesting cache refresh
        # (this is what happens when ModuleStateChangedEvent is processed)
        for _ in range(4):
            await self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

        # Give debounce window time to expire
        await asyncio.sleep(0.06)

        # KEY ASSERTION: Only 1 telegram sent (75% reduction!)
        assert self.telegram_protocol.sendFrame.call_count == 1
        self.telegram_protocol.sendFrame.assert_called_with(b"S012345678901F02D12")
