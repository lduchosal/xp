"""Unit tests for TelegramProtocol debouncing functionality."""

import asyncio
import time
from typing import cast
from unittest.mock import Mock

import pytest
from bubus import EventBus

from xp.services.protocol.telegram_protocol import TelegramProtocol


class TestTelegramProtocolDebounce:
    """Test cases for TelegramProtocol debouncing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.protocol = TelegramProtocol(
            event_bus=self.event_bus,
            debounce_ms=50,
        )
        # Mock transport
        self.protocol.transport = Mock()

    @pytest.mark.asyncio
    async def test_init(self):
        """Test protocol initialization with debounce parameters."""
        protocol = TelegramProtocol(
            event_bus=self.event_bus,
            debounce_ms=100,
        )

        assert protocol.event_bus == self.event_bus
        assert protocol.debounce_ms == 100
        assert protocol.send_queue == {}
        assert protocol.timer_handle is None

    @pytest.mark.asyncio
    async def test_single_frame_sent_immediately(self):
        """First occurrence of frame is sent immediately."""
        data = b"S012345678901F02D12"

        await self.protocol._async_sendFrame(data)

        # Verify transport.write was called
        mock_transport = cast(Mock, self.protocol.transport)
        assert mock_transport.write.call_count == 1
        # Verify frame format: <payload+checksum>
        call_args = mock_transport.write.call_args[0][0]
        assert call_args.startswith(b"<S012345678901F02D12")
        assert call_args.endswith(b">")

    @pytest.mark.asyncio
    async def test_duplicate_within_window_skipped(self):
        """Duplicate frame within debounce window is skipped."""
        data = b"S012345678901F02D12"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send first frame
        await self.protocol._async_sendFrame(data)
        assert mock_transport.write.call_count == 1

        # Send duplicate immediately (within debounce window)
        await self.protocol._async_sendFrame(data)

        # Still only 1 call - duplicate was skipped
        assert mock_transport.write.call_count == 1

    @pytest.mark.asyncio
    async def test_duplicate_outside_window_sent(self):
        """Duplicate frame outside debounce window is sent."""
        data = b"S012345678901F02D12"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send first frame
        await self.protocol._async_sendFrame(data)
        assert mock_transport.write.call_count == 1

        # Wait for debounce window to expire (50ms + buffer)
        await asyncio.sleep(0.06)

        # Send same frame again (outside window)
        await self.protocol._async_sendFrame(data)

        # Should be sent again (2 total calls)
        assert mock_transport.write.call_count == 2

    @pytest.mark.asyncio
    async def test_different_frames_all_sent(self):
        """Different frames are all sent regardless of timing."""
        data1 = b"S012345678901F02D12"
        data2 = b"S012345678901F02D15"
        data3 = b"S987654321098F02D12"
        mock_transport = cast(Mock, self.protocol.transport)

        await self.protocol._async_sendFrame(data1)
        await self.protocol._async_sendFrame(data2)
        await self.protocol._async_sendFrame(data3)

        # All 3 should be sent (different frames)
        assert mock_transport.write.call_count == 3

    @pytest.mark.asyncio
    async def test_burst_deduplication(self):
        """Burst of identical frames -> only first sent."""
        data = b"S012345678901F02D12"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send 4 identical frames in rapid succession
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)

        # Only first should be sent (75% reduction)
        assert mock_transport.write.call_count == 1

    @pytest.mark.asyncio
    async def test_timestamp_tracking(self):
        """Verify timestamps are tracked for sent frames."""
        data = b"S012345678901F02D12"

        await self.protocol._async_sendFrame(data)

        # Check that send_queue has entry
        assert len(self.protocol.send_queue) == 1

        # Get the frame key (with checksum and brackets)
        frame_key = list(self.protocol.send_queue.keys())[0]
        assert frame_key.startswith(b"<S012345678901F02D12")

        # Check timestamp list exists
        assert len(self.protocol.send_queue[frame_key]) == 1

    @pytest.mark.asyncio
    async def test_cleanup_old_timestamps(self):
        """Old timestamps are cleaned up periodically."""
        data = b"S012345678901F02D12"

        # Send frame
        await self.protocol._async_sendFrame(data)
        assert len(self.protocol.send_queue) == 1

        # Manually trigger cleanup with old timestamp
        frame_key = list(self.protocol.send_queue.keys())[0]
        # Set timestamp to 1 second ago (way outside window)
        self.protocol.send_queue[frame_key] = [time.time() - 1.0]

        # Run cleanup
        self.protocol._cleanup_old_timestamps()

        # Frame should be removed from queue
        assert len(self.protocol.send_queue) == 0

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent_timestamps(self):
        """Recent timestamps are kept during cleanup."""
        data = b"S012345678901F02D12"

        # Send frame
        await self.protocol._async_sendFrame(data)
        frame_key = list(self.protocol.send_queue.keys())[0]

        # Run cleanup immediately
        self.protocol._cleanup_old_timestamps()

        # Frame should still be in queue (timestamp is recent)
        assert len(self.protocol.send_queue) == 1
        assert len(self.protocol.send_queue[frame_key]) == 1

    @pytest.mark.asyncio
    async def test_no_transport_raises_error(self):
        """Sending frame without transport raises IOError."""
        protocol = TelegramProtocol(event_bus=self.event_bus, debounce_ms=50)
        protocol.transport = None

        data = b"S012345678901F02D12"

        with pytest.raises(IOError, match="Transport is not open"):
            await protocol._async_sendFrame(data)

    @pytest.mark.asyncio
    async def test_debounce_disabled_with_zero_ms(self):
        """Debouncing can be disabled by setting debounce_ms=0."""
        protocol = TelegramProtocol(event_bus=self.event_bus, debounce_ms=0)
        mock_transport = Mock()
        protocol.transport = mock_transport

        data = b"S012345678901F02D12"

        # Send same frame 3 times
        await protocol._async_sendFrame(data)
        await protocol._async_sendFrame(data)
        await protocol._async_sendFrame(data)

        # With debounce_ms=0, all should be sent (no deduplication)
        assert mock_transport.write.call_count == 3

    @pytest.mark.asyncio
    async def test_multiple_frames_separate_tracking(self):
        """Multiple different frames have separate timestamp tracking."""
        data1 = b"S012345678901F02D12"
        data2 = b"S012345678901F02D15"

        await self.protocol._async_sendFrame(data1)
        await self.protocol._async_sendFrame(data2)

        # Should have 2 separate entries in send_queue
        assert len(self.protocol.send_queue) == 2

    @pytest.mark.asyncio
    async def test_frame_format_with_checksum(self):
        """Verify frame format includes checksum and brackets."""
        data = b"S012345678901F02D12"
        mock_transport = cast(Mock, self.protocol.transport)

        await self.protocol._async_sendFrame(data)

        # Get the actual frame sent
        sent_frame = mock_transport.write.call_args[0][0]

        # Should start with <, end with >, and include checksum
        assert sent_frame.startswith(b"<S012345678901F02D12")
        assert sent_frame.endswith(b">")
        # Checksum should be 2 characters before >
        assert len(sent_frame) > 20

    @pytest.mark.asyncio
    async def test_timer_handle_set_and_cancelled(self):
        """Timer handle is set for cleanup and cancelled on new send."""
        data = b"S012345678901F02D12"

        # Send first frame
        await self.protocol._async_sendFrame(data)
        first_timer = self.protocol.timer_handle

        assert first_timer is not None

        # Wait a bit but not long enough for timer to expire
        await asyncio.sleep(0.01)

        # Send another different frame
        await self.protocol._async_sendFrame(b"S987654321098F02D12")
        second_timer = self.protocol.timer_handle

        # Timer should be replaced
        assert second_timer is not None
        assert second_timer != first_timer

    @pytest.mark.asyncio
    async def test_action_telegram_deduplication(self):
        """Action telegrams (F27) are also deduplicated."""
        # Action telegram: turn on output 2
        data = b"S012345678901F27D02AB"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send same action 3 times (user clicking button rapidly)
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)

        # Only first should be sent
        assert mock_transport.write.call_count == 1

    @pytest.mark.asyncio
    async def test_write_config_telegram_deduplication(self):
        """Write config telegrams (F04) are also deduplicated."""
        # Write config telegram: set brightness
        data = b"S012345678901F04D1502:050"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send same config 2 times (UI sending duplicate commands)
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)

        # Only first should be sent
        assert mock_transport.write.call_count == 1

    @pytest.mark.asyncio
    async def test_discover_telegram_deduplication(self):
        """Discovery telegrams are also deduplicated."""
        # Discover modules telegram
        data = b"S0000000000F01D00"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send same discovery 2 times (reconnection retries)
        await self.protocol._async_sendFrame(data)
        await self.protocol._async_sendFrame(data)

        # Only first should be sent
        assert mock_transport.write.call_count == 1

    @pytest.mark.asyncio
    async def test_deduplication_accuracy_50ms(self):
        """Test exact 50ms debounce window timing."""
        data = b"S012345678901F02D12"
        mock_transport = cast(Mock, self.protocol.transport)

        # Send first frame
        await self.protocol._async_sendFrame(data)
        assert mock_transport.write.call_count == 1

        # Wait exactly 30ms (within window)
        await asyncio.sleep(0.03)
        await self.protocol._async_sendFrame(data)
        assert mock_transport.write.call_count == 1  # Still deduplicated

        # Wait another 30ms (total 60ms, outside window)
        await asyncio.sleep(0.03)
        await self.protocol._async_sendFrame(data)
        assert mock_transport.write.call_count == 2  # Sent again
