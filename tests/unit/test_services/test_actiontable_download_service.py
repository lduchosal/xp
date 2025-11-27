"""Unit tests for ActionTableDownloadService state machine."""

from unittest.mock import Mock

import pytest

from xp.models.actiontable.actiontable import ActionTable
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
    Phase,
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

    def test_error_status_received_transitions_waiting_ok_to_receiving(self, service):
        """Test error_status_received transitions from waiting_ok to receiving."""
        service.do_connect()
        service.do_timeout()  # -> resetting -> waiting_ok
        assert service.waiting_ok.is_active
        service.error_status_received()
        assert service.receiving.is_active

    def test_no_error_status_received_transitions_waiting_ok_to_requesting(
        self, service
    ):
        """Test no_error_status_received transitions from waiting_ok to requesting."""
        service.do_connect()
        service.do_timeout()  # -> resetting -> waiting_ok
        assert service.waiting_ok.is_active
        assert service._phase == Phase.INIT
        service.no_error_status_received()
        # Guard is_init_phase=True -> requesting
        # on_enter_requesting calls send_download -> waiting_data
        assert service.waiting_data.is_active

    def test_receive_chunk_transitions_waiting_data_to_receiving_chunk(self, service):
        """Test receive_chunk event transitions correctly."""
        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()  # -> resetting -> waiting_ok
        service.no_error_status_received()  # -> requesting -> waiting_data
        assert service.waiting_data.is_active

        service.receive_chunk()
        # on_enter_receiving_chunk calls send_ack -> waiting_data
        assert service.waiting_data.is_active

    def test_receive_eof_transitions_to_processing_eof_then_receiving(self, service):
        """Test receive_eof event transitions to processing_eof then receiving (CLEANUP)."""
        # Get to waiting_data state
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()
        assert service.waiting_data.is_active

        service.receive_eof()
        # on_enter_processing_eof sets phase=CLEANUP, calls do_finish -> receiving
        assert service.receiving.is_active
        assert service._phase == Phase.CLEANUP

    def test_no_error_status_received_in_cleanup_phase_goes_to_completed(self, service):
        """Test no_error_status_received in CLEANUP phase goes to completed via guard."""
        # Get to waiting_ok in CLEANUP phase
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()  # -> requesting -> waiting_data
        service.receive_eof()  # -> processing_eof -> receiving (phase=CLEANUP)
        assert service._phase == Phase.CLEANUP
        service.do_timeout()  # -> resetting -> waiting_ok
        assert service.waiting_ok.is_active

        # no_error_status_received with is_cleanup_phase guard -> completed
        service.no_error_status_received()
        assert service.completed.is_active

    def test_full_download_flow(self, service):
        """Test complete download flow through all states."""
        # Start in idle
        assert service.idle.is_active
        assert service._phase == Phase.INIT

        # Phase 1: Connection & Reset Handshake
        service.do_connect()  # idle -> receiving
        assert service.receiving.is_active

        service.do_timeout()  # receiving -> resetting -> waiting_ok
        assert service.waiting_ok.is_active

        service.no_error_status_received()  # waiting_ok -> requesting -> waiting_data
        assert service.waiting_data.is_active
        assert service._phase == Phase.DOWNLOAD

        # Phase 2: Download chunks
        service.receive_chunk()  # waiting_data -> receiving_chunk -> waiting_data
        assert service.waiting_data.is_active

        service.receive_chunk()  # Another chunk
        assert service.waiting_data.is_active

        # Phase 3: EOF and Finalization (reuses receiving/resetting/waiting_ok)
        service.receive_eof()  # waiting_data -> processing_eof -> receiving
        assert service.receiving.is_active
        assert service._phase == Phase.CLEANUP

        service.do_timeout()  # receiving -> resetting -> waiting_ok
        assert service.waiting_ok.is_active

        service.no_error_status_received()  # waiting_ok -> completed (guard: is_cleanup_phase)
        assert service.completed.is_active

    def test_cannot_transition_from_completed(self, service):
        """Test that completed is a final state."""
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()  # -> requesting -> waiting_data
        service.receive_eof()  # -> processing_eof -> receiving (CLEANUP)
        service.do_timeout()  # -> resetting -> waiting_ok
        service.no_error_status_received()  # -> completed
        assert service.completed.is_active

        # In final state, events are silently ignored with allow_event_without_transition=True
        service.do_connect()
        assert service.completed.is_active  # Still in completed

    def test_guard_is_init_phase(self, service):
        """Test is_init_phase guard returns correct value."""
        assert service._phase == Phase.INIT
        assert service.is_init_phase() is True
        assert service.is_cleanup_phase() is False

        service._phase = Phase.CLEANUP
        assert service.is_init_phase() is False
        assert service.is_cleanup_phase() is True


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
        service.no_error_status_received()  # -> requesting -> waiting_data
        service.receive_eof()  # -> processing_eof -> receiving (CLEANUP)
        service.do_timeout()  # -> resetting -> waiting_ok
        service.no_error_status_received()  # -> completed
        assert service.completed.is_active

        # Enter context manager should reset
        with service:
            assert service.idle.is_active

    def test_enter_clears_actiontable_data(self, service):
        """Test __enter__ clears actiontable_data list."""
        service.actiontable_data = ["chunk1", "chunk2"]

        with service:
            assert service.actiontable_data == []

    def test_enter_resets_phase_to_init(self, service):
        """Test __enter__ resets _phase to INIT."""
        service._phase = Phase.CLEANUP

        with service:
            assert service._phase == Phase.INIT

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
