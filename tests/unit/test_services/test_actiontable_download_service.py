"""Unit tests for ActionTableDownloadService state machine."""

from unittest.mock import Mock

import pytest
from statemachine.exceptions import TransitionNotAllowed

from xp.models.actiontable.actiontable import ActionTable
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
)


class TestActionTableDownloadServiceStateMachine:
    """Test state machine behavior of ActionTableDownloadService."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        protocol = Mock()
        protocol.on_connection_made = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_failed.disconnect = Mock()
        protocol.send_telegram = Mock()
        protocol.start_reactor = Mock()
        protocol.stop_reactor = Mock()
        protocol.timeout_seconds = 5.0
        return protocol

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        serializer = Mock()
        # Return a real ActionTable to avoid asdict() errors
        serializer.from_encoded_string = Mock(return_value=ActionTable(entries=[]))
        serializer.format_decoded_output = Mock(return_value=[])
        return serializer

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
        mock_telegram_service,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
        )

    def test_initial_state_is_idle(self, service):
        """Test service starts in idle state."""
        assert service.idle.is_active

    def test_has_9_states(self, service):
        """Test service has all 9 states defined in spec."""
        assert hasattr(service, "idle")
        assert hasattr(service, "receiving")
        assert hasattr(service, "resetting")
        assert hasattr(service, "waiting_ok")
        assert hasattr(service, "requesting")
        assert hasattr(service, "waiting_data")
        assert hasattr(service, "receiving_chunk")
        assert hasattr(service, "processing_eof")
        assert hasattr(service, "completed")

    def test_connect_transitions_idle_to_receiving(self, service):
        """Test do_connect event transitions from idle to receiving."""
        assert service.idle.is_active
        service.do_connect()
        assert service.receiving.is_active

    def test_filter_telegram_self_transition_in_receiving(self, service):
        """Test filter_telegram stays in receiving state (self-transition)."""
        service.do_connect()
        assert service.receiving.is_active
        service.filter_telegram()
        assert service.receiving.is_active  # Still in receiving

    def test_timeout_transitions_receiving_to_resetting(self, service):
        """Test do_timeout transitions from receiving to resetting."""
        service.do_connect()
        assert service.receiving.is_active
        service.do_timeout()
        # on_enter_resetting calls send_error_status -> waiting_ok
        assert service.waiting_ok.is_active

    def test_nak_received_transitions_waiting_ok_to_receiving(self, service):
        """Test nak_received transitions from waiting_ok to receiving."""
        service.do_connect()
        service.do_timeout()  # -> resetting -> waiting_ok
        assert service.waiting_ok.is_active
        service.nak_received()
        assert service.receiving.is_active

    def test_ack_received_transitions_waiting_ok_to_requesting(self, service):
        """Test ack_received transitions from waiting_ok to requesting."""
        service.do_connect()
        service.do_timeout()  # -> resetting -> waiting_ok
        assert service.waiting_ok.is_active
        service.ack_received()
        # on_enter_requesting calls send_download -> waiting_data
        assert service.waiting_data.is_active

    def test_receive_chunk_transitions_waiting_data_to_receiving_chunk(self, service):
        """Test receive_chunk event transitions correctly."""
        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()  # -> resetting -> waiting_ok
        service.ack_received()  # -> requesting -> waiting_data
        assert service.waiting_data.is_active

        service.receive_chunk()
        # on_enter_receiving_chunk calls send_ack -> waiting_data
        assert service.waiting_data.is_active

    def test_receive_eof_transitions_to_processing_eof(self, service):
        """Test receive_eof event transitions to processing_eof."""
        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()
        service.ack_received()
        assert service.waiting_data.is_active

        service.receive_eof()
        # on_enter_processing_eof calls do_finish -> receiving
        assert service.receiving.is_active

    def test_ack_received_with_download_complete_transitions_to_completed(self, service):
        """Test ack_received with download complete goes to completed (guard condition)."""
        # Get to waiting_ok after download
        service.do_connect()
        service.do_timeout()
        service.ack_received()  # -> requesting -> waiting_data (download pending)
        service.receive_eof()  # -> processing_eof -> receiving (_download_complete = True)
        service.do_timeout()  # -> resetting -> waiting_ok
        assert service.waiting_ok.is_active
        assert service._download_complete is True

        # ack_received now goes to completed due to guard condition
        service.ack_received()
        assert service.completed.is_active

    def test_full_download_flow(self, service):
        """Test complete download flow through all states."""
        # Start in idle
        assert service.idle.is_active

        # Phase 1: Connection & Reset Handshake
        service.do_connect()  # idle -> receiving
        assert service.receiving.is_active

        service.do_timeout()  # receiving -> resetting -> waiting_ok
        assert service.waiting_ok.is_active

        service.ack_received()  # waiting_ok -> requesting -> waiting_data
        assert service.waiting_data.is_active

        # Phase 2: Download chunks
        service.receive_chunk()  # waiting_data -> receiving_chunk -> waiting_data
        assert service.waiting_data.is_active

        service.receive_chunk()  # Another chunk
        assert service.waiting_data.is_active

        # Phase 3: EOF and Finalization
        service.receive_eof()  # waiting_data -> processing_eof -> receiving
        assert service.receiving.is_active

        service.do_timeout()  # receiving -> resetting -> waiting_ok
        assert service.waiting_ok.is_active

        service.ack_received()  # waiting_ok -> completed (guard: download complete)
        assert service.completed.is_active

    def test_cannot_transition_from_completed(self, service):
        """Test that completed is a final state."""
        service.do_connect()
        service.do_timeout()
        service._download_complete = True  # Set guard condition
        service.ack_received()  # -> completed
        assert service.completed.is_active

        with pytest.raises(TransitionNotAllowed):
            service.do_connect()


class TestActionTableDownloadServiceProtocolIntegration:
    """Test protocol signal integration with state machine."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        protocol = Mock()
        protocol.on_connection_made = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_failed.disconnect = Mock()
        protocol.send_telegram = Mock()
        protocol.start_reactor = Mock()
        protocol.stop_reactor = Mock()
        protocol.timeout_seconds = 5.0
        return protocol

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        serializer = Mock()
        # Return a real ActionTable to avoid asdict() errors
        serializer.from_encoded_string = Mock(return_value=ActionTable(entries=[]))
        serializer.format_decoded_output = Mock(return_value=[])
        return serializer

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
        mock_telegram_service,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
        )

    def test_connection_made_triggers_connect(self, service):
        """Test _on_connection_made triggers do_connect transition."""
        assert service.idle.is_active
        service._on_connection_made()
        assert service.receiving.is_active

    def test_timeout_in_receiving_triggers_reset(self, service):
        """Test _on_timeout in receiving triggers reset flow."""
        service.do_connect()
        assert service.receiving.is_active

        service._on_timeout()
        # Should transition through resetting to waiting_ok
        assert service.waiting_ok.is_active

    def test_timeout_in_waiting_ok_triggers_retry(self, service):
        """Test _on_timeout in waiting_ok retries via nak_received."""
        service.do_connect()
        service.do_timeout()
        assert service.waiting_ok.is_active

        service._on_timeout()
        # Should go back to receiving for retry
        assert service.receiving.is_active

    def test_signals_connected_on_init(self, mock_conbus_protocol):
        """Test that protocol signals are connected on initialization."""
        mock_serializer = Mock()
        mock_telegram_service = Mock()

        ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
        )

        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()


class TestActionTableDownloadServiceContextManager:
    """Test context manager behavior."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        protocol = Mock()
        protocol.on_connection_made = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_failed.disconnect = Mock()
        protocol.send_telegram = Mock()
        protocol.start_reactor = Mock()
        protocol.stop_reactor = Mock()
        protocol.timeout_seconds = 5.0
        return protocol

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        serializer = Mock()
        # Return a real ActionTable to avoid asdict() errors
        serializer.from_encoded_string = Mock(return_value=ActionTable(entries=[]))
        serializer.format_decoded_output = Mock(return_value=[])
        return serializer

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
        mock_telegram_service,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            telegram_service=mock_telegram_service,
        )

    def test_enter_resets_state_to_idle(self, service):
        """Test __enter__ resets state machine to idle."""
        # Progress through states
        service.do_connect()
        service.do_timeout()
        service._download_complete = True  # Set guard condition
        service.ack_received()  # -> completed
        assert service.completed.is_active

        # Enter context manager should reset
        with service:
            assert service.idle.is_active

    def test_enter_clears_actiontable_data(self, service):
        """Test __enter__ clears actiontable_data list."""
        service.actiontable_data = ["chunk1", "chunk2"]

        with service:
            assert service.actiontable_data == []

    def test_enter_clears_download_complete_flag(self, service):
        """Test __enter__ clears _download_complete flag."""
        service._download_complete = True

        with service:
            assert service._download_complete is False

    def test_exit_disconnects_signals(self, service, mock_conbus_protocol):
        """Test __exit__ disconnects protocol signals."""
        with service:
            pass

        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()

    def test_exit_stops_reactor(self, service, mock_conbus_protocol):
        """Test __exit__ stops reactor."""
        with service:
            pass

        mock_conbus_protocol.stop_reactor.assert_called_once()
