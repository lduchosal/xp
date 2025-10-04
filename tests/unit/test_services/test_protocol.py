from unittest.mock import Mock

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
    """Test cases for TelegramProtocol"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.protocol = TelegramProtocol(self.event_bus)
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)

    def test_init(self):
        """Test protocol initialization"""
        event_bus = Mock(spec=EventBus)
        protocol = TelegramProtocol(event_bus)

        assert protocol.buffer == b""
        assert protocol.event_bus == event_bus
        assert protocol.logger is not None

    def test_connection_made(self):
        """Test connectionMade dispatches ConnectionMadeEvent"""
        self.event_bus.dispatch.assert_called_once()
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, ConnectionMadeEvent)
        assert call_args.protocol == self.protocol

    def test_data_received_single_complete_frame(self):
        """Test receiving a single complete frame"""
        # Create a frame with valid checksum (TEST checksum is BG)
        self.protocol.dataReceived(b"<TESTBG>")

        # Should dispatch TelegramReceivedEvent
        assert self.event_bus.dispatch.call_count == 2  # 1 for connection, 1 for frame
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.protocol == self.protocol
        assert call_args.telegram == "TEST"
        assert call_args.raw_frame == "<TEST>"

    def test_data_received_multiple_frames(self):
        """Test receiving multiple frames in one data chunk"""
        # TEST checksum is BG, DATA checksum is BA
        self.protocol.dataReceived(b"<TESTBG><DATABA>")

        # Should dispatch 2 TelegramReceivedEvents (plus 1 ConnectionMadeEvent)
        assert self.event_bus.dispatch.call_count == 3

        # Check first frame
        first_call = self.event_bus.dispatch.call_args_list[1][0][0]
        assert isinstance(first_call, TelegramReceivedEvent)
        assert first_call.telegram == "TEST"

        # Check second frame
        second_call = self.event_bus.dispatch.call_args_list[2][0][0]
        assert isinstance(second_call, TelegramReceivedEvent)
        assert second_call.telegram == "DATA"

    def test_data_received_partial_frame(self):
        """Test receiving partial frame data"""
        # Send first part
        self.protocol.dataReceived(b"<TE")
        assert self.event_bus.dispatch.call_count == 1  # Only ConnectionMadeEvent

        # Send rest of frame (TEST checksum is BG)
        self.protocol.dataReceived(b"STBG>")
        assert self.event_bus.dispatch.call_count == 2  # Now TelegramReceivedEvent too

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "TEST"

    def test_data_received_no_start_delimiter(self):
        """Test receiving data without start delimiter"""
        self.protocol.dataReceived(b"NOSTART>")

        # Should not dispatch any telegram event, only ConnectionMadeEvent
        assert self.event_bus.dispatch.call_count == 1

    def test_data_received_no_end_delimiter(self):
        """Test receiving data without end delimiter"""
        self.protocol.dataReceived(b"<NOEND")

        # Should buffer the data but not dispatch
        assert self.event_bus.dispatch.call_count == 1  # Only ConnectionMadeEvent
        assert self.protocol.buffer == b"<NOEND"

    def test_data_received_invalid_checksum(self):
        """Test receiving frame with invalid checksum"""
        # Create a frame with invalid checksum
        self.protocol.dataReceived(b"<TESTXX>")

        # Should dispatch InvalidTelegramReceivedEvent
        assert self.event_bus.dispatch.call_count == 2
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, InvalidTelegramReceivedEvent)
        assert call_args.protocol == self.protocol

    def test_data_received_buffer_accumulation(self):
        """Test that buffer accumulates data correctly"""
        self.protocol.dataReceived(b"<TE")
        assert self.protocol.buffer == b"<TE"

        self.protocol.dataReceived(b"ST12>")
        # After processing, buffer should be empty
        assert self.protocol.buffer == b""

    def test_data_received_junk_before_frame(self):
        """Test receiving junk data before valid frame"""
        # TEST checksum is BG
        self.protocol.dataReceived(b"JUNK<TESTBG>")

        # Should still process the frame correctly
        assert self.event_bus.dispatch.call_count == 2
        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "TEST"

    def test_data_received_multiple_frames_with_junk(self):
        """Test receiving multiple frames with junk data"""
        # TEST checksum is BG, DATA checksum is BA
        self.protocol.dataReceived(b"JUNK<TESTBG>MORE<DATABA>")

        # Should process both frames
        assert self.event_bus.dispatch.call_count == 3  # 1 connection + 2 frames

    def test_frame_received(self):
        """Test frameReceived method directly"""
        frame = b"HELLO"
        self.protocol.frameReceived(frame)

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "HELLO"
        assert call_args.raw_frame == "<HELLO>"

    def test_send_frame(self):
        """Test sending a frame with checksum"""
        self.protocol.sendFrame(b"TEST")

        # Check what was written to transport
        sent_data = self.transport.value()
        assert sent_data.startswith(b"<TEST")
        assert sent_data.endswith(b">")
        assert len(sent_data) == 8  # <TEST + 2 char checksum + >

    def test_send_frame_no_transport(self):
        """Test sending frame when transport is not available"""
        protocol = TelegramProtocol(self.event_bus)
        # Don't connect transport
        protocol.sendFrame(b"TEST")

        # Should not raise an error, just log

    def test_send_frame_includes_checksum(self):
        """Test that sendFrame calculates and includes checksum"""
        self.protocol.sendFrame(b"DATA")

        sent_data = self.transport.value()
        # Frame should be <DATA + checksum + >
        assert sent_data.startswith(b"<DATA")
        assert sent_data.endswith(b">")
        # Checksum should be 2 characters between DATA and >
        assert len(sent_data) == 8  # <DATA + 2 char checksum + >


class TestTelegramFactory:
    """Test cases for TelegramFactory"""

    def setup_method(self):
        """Setup test fixtures"""
        self.event_bus = Mock(spec=EventBus)
        self.telegram_protocol = Mock(spec=TelegramProtocol)
        self.factory = TelegramFactory(self.event_bus, self.telegram_protocol)

    def test_init(self):
        """Test factory initialization"""
        event_bus = Mock(spec=EventBus)
        telegram_protocol = Mock(spec=TelegramProtocol)

        factory = TelegramFactory(event_bus, telegram_protocol)

        assert factory.event_bus == event_bus
        assert factory.telegram_protocol == telegram_protocol
        assert factory.logger is not None

    def test_build_protocol(self):
        """Test buildProtocol returns the configured protocol"""
        addr = Mock(spec=IAddress)

        protocol = self.factory.buildProtocol(addr)

        assert protocol == self.telegram_protocol

    def test_client_connection_failed(self):
        """Test clientConnectionFailed dispatches event and stops connector"""
        connector = Mock(spec=IConnector)
        connector.stop = Mock()
        reason = Failure(Exception("Connection failed"))

        self.factory.clientConnectionFailed(connector, reason)

        # Should dispatch ConnectionFailedEvent
        self.event_bus.dispatch.assert_called_once()
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, ConnectionFailedEvent)
        assert "Connection failed" in call_args.reason

        # Should stop the connector
        connector.stop.assert_called_once()

    def test_client_connection_lost(self):
        """Test clientConnectionLost dispatches event and stops connector"""
        connector = Mock(spec=IConnector)
        connector.stop = Mock()
        reason = Failure(Exception("Connection lost"))

        self.factory.clientConnectionLost(connector, reason)

        # Should dispatch ConnectionLostEvent
        self.event_bus.dispatch.assert_called_once()
        call_args = self.event_bus.dispatch.call_args[0][0]

        assert isinstance(call_args, ConnectionLostEvent)
        assert "Connection lost" in call_args.reason

        # Should stop the connector
        connector.stop.assert_called_once()

    def test_client_connection_failed_reason_conversion(self):
        """Test that Failure reason is converted to string in ConnectionFailedEvent"""
        connector = Mock(spec=IConnector)
        connector.stop = Mock()
        reason = Failure(ConnectionRefusedError("Port closed"))

        self.factory.clientConnectionFailed(connector, reason)

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args.reason, str)
        assert len(call_args.reason) > 0

    def test_client_connection_lost_reason_conversion(self):
        """Test that Failure reason is converted to string in ConnectionLostEvent"""
        connector = Mock(spec=IConnector)
        connector.stop = Mock()
        reason = Failure(ConnectionError("Network error"))

        self.factory.clientConnectionLost(connector, reason)

        call_args = self.event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args.reason, str)
        assert len(call_args.reason) > 0


class TestTelegramProtocolIntegration:
    """Integration tests for TelegramProtocol with event bus"""

    def test_full_flow_receive_and_send(self):
        """Test full flow of receiving and sending telegrams"""
        event_bus = Mock(spec=EventBus)
        protocol = TelegramProtocol(event_bus)
        transport = proto_helpers.StringTransport()
        protocol.makeConnection(transport)

        # Receive a frame
        protocol.dataReceived(b"<TEST12>")

        # Send a frame
        protocol.sendFrame(b"REPLY")

        # Verify events were dispatched
        assert event_bus.dispatch.call_count == 2  # ConnectionMade + TelegramReceived

        # Verify data was sent
        sent_data = transport.value()
        assert sent_data.startswith(b"<REPLY")
        assert sent_data.endswith(b">")

    def test_protocol_event_bus_integration(self):
        """Test that protocol correctly dispatches events to event bus"""
        event_bus = Mock(spec=EventBus)
        protocol = TelegramProtocol(event_bus)
        transport = proto_helpers.StringTransport()
        protocol.makeConnection(transport)

        # Clear the connection made event
        event_bus.dispatch.reset_mock()

        # Receive a frame (DATA checksum is BA)
        protocol.dataReceived(b"<DATABA>")

        # Verify TelegramReceivedEvent was dispatched
        event_bus.dispatch.assert_called_once()
        call_args = event_bus.dispatch.call_args[0][0]
        assert isinstance(call_args, TelegramReceivedEvent)
        assert call_args.telegram == "DATA"
        assert call_args.protocol == protocol
