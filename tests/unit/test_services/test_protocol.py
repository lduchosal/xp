"""Unit tests for protocol handling."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from bubus import EventBus
from twisted.internet.interfaces import IAddress, IConnector
from twisted.python.failure import Failure
from twisted.test import proto_helpers

from xp.models.protocol.conbus_protocol import (
    ConnectionFailedEvent,
    ConnectionLostEvent,
    ConnectionMadeEvent,
    InvalidTelegramReceivedEvent,
    TelegramReceivedEvent,
)
from xp.services.protocol.protocol_factory import TelegramFactory
from xp.services.protocol.telegram_protocol import TelegramProtocol


class TestTelegramProtocol:
    """Test cases for TelegramProtocol."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.event_bus.dispatch = AsyncMock()
        self.protocol = TelegramProtocol(self.event_bus)
        self.transport = proto_helpers.StringTransport()

    def test_init(self):
        """Test protocol initialization."""
        event_bus = Mock(spec=EventBus)
        protocol = TelegramProtocol(event_bus)

        assert protocol.buffer == b""
        assert protocol.event_bus == event_bus
        assert protocol.logger is not None

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_connection_made(self):
        """Test connectionMade dispatches ConnectionMadeEvent."""
        self.protocol.makeConnection(self.transport)

        # Wait for the async task to complete
        await asyncio.sleep(0.01)
        self.event_bus.dispatch.assert_called_once()
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, ConnectionMadeEvent)
        assert call_args.protocol == self.protocol

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_single_complete_frame(self):
        """Test receiving a single complete frame."""
        self.protocol.makeConnection(self.transport)

        # Create a frame with valid checksum (TEST checksum is BG)
        self.protocol.dataReceived(b"<TESTBG>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should dispatch TelegramReceivedEvent
        assert self.event_bus.dispatch.call_count == 2  # 1 for connection, 1 for frame
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.protocol == self.protocol
        assert call_args.telegram == "TESTBG"
        assert call_args.frame == "<TESTBG>"

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_multiple_frames(self):
        """Test receiving multiple frames in one data chunk."""
        self.protocol.makeConnection(self.transport)

        # TEST checksum is BG, DATA checksum is BA
        self.protocol.dataReceived(b"<TESTBG><DATABA>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should dispatch 2 TelegramReceivedEvents (plus 1 ConnectionMadeEvent)
        assert self.event_bus.dispatch.call_count == 3

        # Check first frame
        first_call = self.event_bus.dispatch.call_args_list[1][0][0]
        assert isinstance(first_call, TelegramReceivedEvent)
        assert first_call.telegram == "TESTBG"

        # Check second frame
        second_call = self.event_bus.dispatch.call_args_list[2][0][0]
        assert isinstance(second_call, TelegramReceivedEvent)
        assert second_call.telegram == "DATABA"

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_partial_frame(self):
        """Test receiving partial frame data."""
        self.protocol.makeConnection(self.transport)

        # Send first part
        self.protocol.dataReceived(b"<TE")
        await asyncio.sleep(0.01)
        assert self.event_bus.dispatch.call_count == 1  # Only ConnectionMadeEvent

        # Send rest of frame (TEST checksum is BG)
        self.protocol.dataReceived(b"STBG>")
        await asyncio.sleep(0.01)
        assert self.event_bus.dispatch.call_count == 2  # Now TelegramReceivedEvent too

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "TESTBG"

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_no_start_delimiter(self):
        """Test receiving data without start delimiter."""
        self.protocol.makeConnection(self.transport)

        self.protocol.dataReceived(b"NOSTART>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should not dispatch any telegram event, only ConnectionMadeEvent
        assert self.event_bus.dispatch.call_count == 1

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_no_end_delimiter(self):
        """Test receiving data without end delimiter."""
        self.protocol.makeConnection(self.transport)

        self.protocol.dataReceived(b"<NOEND")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should buffer the data but not dispatch
        assert self.event_bus.dispatch.call_count == 1  # Only ConnectionMadeEvent
        assert self.protocol.buffer == b"<NOEND"

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_invalid_checksum(self):
        """Test receiving frame with invalid checksum."""
        self.protocol.makeConnection(self.transport)

        # Create a frame with invalid checksum
        self.protocol.dataReceived(b"<TESTXX>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should dispatch InvalidTelegramReceivedEvent
        assert self.event_bus.dispatch.call_count == 2
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, InvalidTelegramReceivedEvent)
        assert call_args.protocol == self.protocol

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_buffer_accumulation(self):
        """Test that buffer accumulates data correctly."""
        self.protocol.makeConnection(self.transport)

        self.protocol.dataReceived(b"<TE")
        await asyncio.sleep(0.01)
        assert self.protocol.buffer == b"<TE"

        self.protocol.dataReceived(b"ST12>")
        await asyncio.sleep(0.01)
        # After processing, buffer should be empty
        assert self.protocol.buffer == b""

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_junk_before_frame(self):
        """Test receiving junk data before valid frame."""
        self.protocol.makeConnection(self.transport)

        # TEST checksum is BG
        self.protocol.dataReceived(b"JUNK<TESTBG>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should still process the frame correctly
        assert self.event_bus.dispatch.call_count == 2
        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "TESTBG"

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_data_received_multiple_frames_with_junk(self):
        """Test receiving multiple frames with junk data."""
        self.protocol.makeConnection(self.transport)

        # TEST checksum is BG, DATA checksum is BA
        self.protocol.dataReceived(b"JUNK<TESTBG>MORE<DATABA>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Should process both frames
        assert self.event_bus.dispatch.call_count == 3  # 1 connection + 2 frames

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_send_frame(self):
        """Test sending a frame with checksum."""
        self.protocol.makeConnection(self.transport)
        self.protocol.sendFrame(b"TEST")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Check what was written to transport
        sent_data = self.transport.value()
        assert sent_data.startswith(b"<TEST")
        assert sent_data.endswith(b">")
        assert len(sent_data) == 8  # <TEST + 2 char checksum + >

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_send_frame_no_transport(self):
        """Test sending frame when transport is not available."""
        protocol = TelegramProtocol(self.event_bus)
        # Don't connect transport
        protocol.sendFrame(b"TEST")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # The error should be logged, not raised synchronously
        # Since the error occurs in the async task, we can't catch it with pytest.raises
        # The protocol should handle this gracefully

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_send_frame_includes_checksum(self):
        """Test that sendFrame calculates and includes checksum."""
        self.protocol.makeConnection(self.transport)
        self.protocol.sendFrame(b"DATA")

        # Wait for async processing
        await asyncio.sleep(0.01)

        sent_data = self.transport.value()
        # Frame should be <DATA + checksum + >
        assert sent_data.startswith(b"<DATA")
        assert sent_data.endswith(b">")
        # Checksum should be 2 characters between DATA and >
        assert len(sent_data) == 8  # <DATA + 2 char checksum + >


class TestTelegramFactory:
    """Test cases for TelegramFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=EventBus)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.connector = Mock(spec=IConnector)
        self.connector.stop = Mock()
        self.factory = TelegramFactory(
            self.event_bus, self.telegram_protocol, self.connector
        )

    def test_init(self):
        """Test factory initialization."""
        event_bus = Mock(spec=EventBus)
        telegram_protocol = Mock(spec=TelegramProtocol)
        connector = Mock(spec=IConnector)

        factory = TelegramFactory(event_bus, telegram_protocol, connector)

        assert factory.event_bus == event_bus
        assert factory.telegram_protocol == telegram_protocol
        assert factory.connector == connector
        assert factory.logger is not None

    def test_build_protocol(self):
        """Test buildProtocol returns the configured protocol."""
        addr = Mock(spec=IAddress)

        protocol = self.factory.buildProtocol(addr)

        assert protocol == self.telegram_protocol

    def test_client_connection_failed(self):
        """Test clientConnectionFailed dispatches event and stops connector."""
        connector = Mock(spec=IConnector)
        reason = Failure(Exception("Connection failed"))

        self.factory.clientConnectionFailed(connector, reason)

        # Should dispatch ConnectionFailedEvent
        self.event_bus.dispatch.assert_called_once()
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, ConnectionFailedEvent)
        assert "Connection failed" in call_args.reason

        # Should stop the factory's connector
        self.connector.stop.assert_called_once()

    def test_client_connection_lost(self):
        """Test clientConnectionLost dispatches event and stops connector."""
        connector = Mock(spec=IConnector)
        reason = Failure(Exception("Connection lost"))

        self.factory.clientConnectionLost(connector, reason)

        # Should dispatch ConnectionLostEvent
        self.event_bus.dispatch.assert_called_once()
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, ConnectionLostEvent)
        assert "Connection lost" in call_args.reason

        # Should stop the factory's connector
        self.connector.stop.assert_called_once()

    def test_client_connection_failed_reason_conversion(self):
        """Test that Failure reason is converted to string in ConnectionFailedEvent."""
        connector = Mock(spec=IConnector)
        reason = Failure(ConnectionRefusedError("Port closed"))

        self.factory.clientConnectionFailed(connector, reason)

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args.reason, str)
        assert len(call_args.reason) > 0
        self.connector.stop.assert_called_once()

    def test_client_connection_lost_reason_conversion(self):
        """Test that Failure reason is converted to string in ConnectionLostEvent."""
        connector = Mock(spec=IConnector)
        reason = Failure(ConnectionError("Network error"))

        self.factory.clientConnectionLost(connector, reason)

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args.reason, str)
        assert len(call_args.reason) > 0
        self.connector.stop.assert_called_once()


class TestTelegramProtocolIntegration:
    """Integration tests for TelegramProtocol with event bus."""

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_full_flow_receive_and_send(self):
        """Test full flow of receiving and sending telegrams."""
        event_bus = Mock(spec=EventBus)
        event_bus.dispatch = AsyncMock()
        protocol = TelegramProtocol(event_bus)
        transport = proto_helpers.StringTransport()
        protocol.makeConnection(transport)

        # Receive a frame
        protocol.dataReceived(b"<TEST12>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Send a frame
        protocol.sendFrame(b"REPLY")

        # Wait for async send processing
        await asyncio.sleep(0.01)

        # Verify events were dispatched
        assert event_bus.dispatch.call_count == 2  # ConnectionMade + TelegramReceived

        # Verify data was sent
        sent_data = transport.value()
        assert sent_data.startswith(b"<REPLY")
        assert sent_data.endswith(b">")

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_protocol_event_bus_integration(self):
        """Test that protocol correctly dispatches events to event bus."""
        event_bus = Mock(spec=EventBus)
        event_bus.dispatch = AsyncMock()
        protocol = TelegramProtocol(event_bus)
        transport = proto_helpers.StringTransport()
        protocol.makeConnection(transport)

        # Wait for connection event to process
        await asyncio.sleep(0.01)

        # Clear the connection made event
        event_bus.dispatch.reset_mock()

        # Receive a frame (DATA checksum is BA)
        protocol.dataReceived(b"<DATABA>")

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Verify TelegramReceivedEvent was dispatched
        event_bus.dispatch.assert_called_once()
        call_args = event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "DATABA"
        assert call_args.protocol == protocol
