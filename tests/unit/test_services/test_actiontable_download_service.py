"""Unit tests for ActionTableDownloadService state machine."""

from typing import List
from unittest.mock import Mock

import pytest

from xp.models.actiontable.actiontable import ActionTable
from xp.models.actiontable.actiontable_type import ActionTableType
from xp.services.actiontable.download_state_machine import (
    MAX_ERROR_RETRIES,
    Phase,
)
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
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
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
        """Test receive_eof event transitions to processing_eof then receiving
        (CLEANUP).
        """
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
        """Test no_error_status_received in CLEANUP phase goes to completed via
        guard.
        """
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
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
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

        ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
        )

        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
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
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
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
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()

    def test_exit_stops_reactor(self, service, mock_conbus_protocol):
        """Test __exit__ stops reactor."""
        with service:
            pass

        mock_conbus_protocol.stop_reactor.assert_called_once()


class TestActionTableDownloadServiceErrorHandling:
    """Test error handling and edge cases."""

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
        protocol.wait = Mock()
        return protocol

    @pytest.fixture
    def mock_serializer(self):
        """Create mock ActionTableSerializer."""
        serializer = Mock()
        serializer.from_encoded_string = Mock(return_value=ActionTable(entries=[]))
        serializer.format_decoded_output = Mock(return_value=[])
        return serializer

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol,
        mock_serializer,
    ):
        """Create service instance for testing."""
        return ActionTableDownloadService(
            conbus_protocol=mock_conbus_protocol,
            actiontable_serializer=mock_serializer,
            msactiontable_serializer_xp20=Mock(),
            msactiontable_serializer_xp24=Mock(),
            msactiontable_serializer_xp33=Mock(),
        )

    def test_failed_handler_emits_error(self, service):
        """Test _on_failed emits error signal."""
        error_received: List[str] = []
        service.on_error.connect(error_received.append)

        service._on_failed("Connection refused")

        assert len(error_received) == 1
        assert error_received[0] == "Connection refused"

    def test_timeout_in_waiting_data_emits_error(self, service):
        """Test timeout in waiting_data state emits error."""
        # Get to waiting_data
        service.do_connect()
        service.do_timeout()
        service.no_error_status_received()
        assert service.waiting_data.is_active

        error_received: List[str] = []
        service.on_error.connect(error_received.append)

        service._on_timeout()

        assert len(error_received) == 1
        assert "Timeout waiting for actiontable data" in error_received[0]

    def test_timeout_in_other_state_emits_error(self, service):
        """Test timeout in non-recoverable state emits error."""
        # Stay in idle (non-recoverable for timeout)
        assert service.idle.is_active

        error_received: List[str] = []
        service.on_error.connect(error_received.append)

        service._on_timeout()

        assert len(error_received) == 1
        assert error_received[0] == "Timeout"

    def test_can_retry_guard_limits_retries(self, service):
        """Test can_retry guard blocks after MAX_ERROR_RETRIES."""
        # Test can_retry guard directly
        assert service.can_retry() is True

        # Set retry count to max
        service._error_retry_count = MAX_ERROR_RETRIES
        assert service.can_retry() is False

        # Reset and verify
        service._error_retry_count = MAX_ERROR_RETRIES - 1
        assert service.can_retry() is True

    def test_configure_sets_serial_number(self, service):
        """Test configure sets serial_number."""
        service.configure(
            serial_number="12345678",
            actiontable_type=ActionTableType.ACTIONTABLE,
        )
        assert service.serial_number == "12345678"

    def test_configure_sets_timeout(self, service, mock_conbus_protocol):
        """Test configure sets timeout."""
        service.configure(
            serial_number="12345678",
            actiontable_type=ActionTableType.ACTIONTABLE,
            timeout_seconds=10.0,
        )
        assert mock_conbus_protocol.timeout_seconds == 10.0

    def test_configure_raises_when_not_idle(self, service):
        """Test configure raises when not in idle state."""
        service.do_connect()
        assert service.receiving.is_active

        with pytest.raises(RuntimeError, match="Cannot configure while download"):
            service.configure(
                serial_number="12345678",
                actiontable_type=ActionTableType.ACTIONTABLE,
            )

    def test_set_timeout(self, service, mock_conbus_protocol):
        """Test set_timeout updates protocol timeout."""
        service.set_timeout(15.0)
        assert mock_conbus_protocol.timeout_seconds == 15.0

    def test_start_reactor_delegates(self, service, mock_conbus_protocol):
        """Test start_reactor calls protocol."""
        service.start_reactor()
        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor_delegates(self, service, mock_conbus_protocol):
        """Test stop_reactor calls protocol."""
        service.stop_reactor()
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_connection_made_ignored_when_not_idle(self, service):
        """Test _on_connection_made is ignored when not in idle state."""
        service.do_connect()
        assert service.receiving.is_active

        # Should not error or change state
        service._on_connection_made()
        assert service.receiving.is_active

    def test_enter_resets_error_retry_count(self, service):
        """Test __enter__ resets error retry count."""
        service._error_retry_count = 5

        with service:
            assert service._error_retry_count == 0
