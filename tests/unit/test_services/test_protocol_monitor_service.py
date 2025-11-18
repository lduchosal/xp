"""Unit tests for ProtocolMonitorService."""

from unittest.mock import Mock

import pytest
from twisted.python.failure import Failure

from xp.models.term.connection_state import ConnectionState
from xp.models.term.protocol_keys_config import ProtocolKeyConfig, ProtocolKeysConfig
from xp.services.term.protocol_monitor_service import ProtocolMonitorService


class TestProtocolMonitorService:
    """Unit tests for ProtocolMonitorService."""

    @pytest.fixture
    def mock_protocol(self):
        """Create mock ConbusEventProtocol."""
        protocol = Mock()
        protocol.cli_config = Mock()
        protocol.cli_config.ip = "192.168.1.100"
        protocol.cli_config.port = 10001
        protocol.transport = None
        protocol.on_connection_made = Mock()
        protocol.on_connection_failed = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_timeout = Mock()
        protocol.on_failed = Mock()
        protocol.connect = Mock()
        protocol.disconnect = Mock()
        protocol.send_raw_telegram = Mock()
        return protocol

    @pytest.fixture
    def protocol_keys(self):
        """Create protocol keys config."""
        return ProtocolKeysConfig(
            protocol={
                "1": ProtocolKeyConfig(
                    name="Discover", telegrams=["S0000000000F01D00"]
                ),
                "2": ProtocolKeyConfig(name="Blink", telegrams=["B01"]),
            }
        )

    @pytest.fixture
    def service(self, mock_protocol, protocol_keys):
        """Create service instance."""
        return ProtocolMonitorService(
            conbus_protocol=mock_protocol, protocol_keys=protocol_keys
        )

    def test_initialization(self, service, mock_protocol):
        """Test service initialization connects signals and sets initial state."""
        assert service.connection_state == ConnectionState.DISCONNECTED
        assert service.server_info == "192.168.1.100:10001"
        mock_protocol.on_connection_made.connect.assert_called_once()
        mock_protocol.on_connection_failed.connect.assert_called_once()

    def test_toggle_connection_when_disconnected(self, service, mock_protocol):
        """Test toggle_connection calls _connect when disconnected."""
        service.toggle_connection()
        mock_protocol.connect.assert_called_once()
        assert service.connection_state == ConnectionState.CONNECTING

    def test_toggle_connection_when_connected(self, service, mock_protocol):
        """Test toggle_connection calls _disconnect when connected."""
        # First connect properly through state machine
        service.toggle_connection()  # DISCONNECTED -> CONNECTING
        service._on_connection_made()  # CONNECTING -> CONNECTED

        # Now toggle should disconnect
        service.toggle_connection()
        mock_protocol.disconnect.assert_called_once()

    def test_handle_key_press_valid_key(self, service, mock_protocol):
        """Test handle_key_press sends telegrams for valid keys."""
        result = service.handle_key_press("1")

        assert result is True
        mock_protocol.send_raw_telegram.assert_called_once_with("S0000000000F01D00")

    def test_handle_key_press_invalid_key(self, service):
        """Test handle_key_press returns False for invalid keys."""
        result = service.handle_key_press("invalid")
        assert result is False

    def test_on_connection_made_handler(self, service):
        """Test _on_connection_made updates state and emits signals."""
        # Must be in CONNECTING state first for transition to work
        service._connect()
        service._on_connection_made()

        assert service.connection_state == ConnectionState.CONNECTED

    def test_on_connection_failed_handler(self, service):
        """Test _on_connection_failed updates state."""
        failure = Failure(Exception("Connection error"))
        service._on_connection_failed(failure)

        assert service.connection_state == ConnectionState.DISCONNECTED

    def test_on_telegram_sent_handler(self, service):
        """Test _on_telegram_sent emits display event."""
        service._on_telegram_sent("<S0000000000F01D00FA>")
        # Just verify it doesn't crash

    def test_on_timeout_handler(self, service):
        """Test _on_timeout logs debug message."""
        service._on_timeout()
        # Just verify it doesn't crash

    def test_on_failed_handler(self, service):
        """Test _on_failed updates state."""
        # Must be in valid state for transition to FAILED
        service._connect()  # DISCONNECTED -> CONNECTING
        service._on_failed("Connection lost")
        assert service.connection_state == ConnectionState.FAILED

    def test_get_keys(self, service):
        """Test get_keys returns protocol keys."""
        keys = dict(service.get_keys())
        assert "1" in keys
        assert "2" in keys
        assert keys["1"].name == "Discover"

    def test_context_manager(self, service, mock_protocol):
        """Test context manager entry and exit."""
        with service as svc:
            assert svc is service

        # Verify cleanup was called
        mock_protocol.on_connection_made.disconnect.assert_called_once()

    def test_send_telegram_error_handling(self, service, mock_protocol):
        """Test _send_telegram handles exceptions."""
        mock_protocol.send_raw_telegram.side_effect = Exception("Send failed")

        service._send_telegram("Test", "TELEGRAM")
        # Should not raise, just log error

    def test_cleanup_with_transport(self, service, mock_protocol):
        """Test cleanup disconnects when transport exists."""
        mock_protocol.transport = Mock()
        # Set up proper connected state through state machine
        service._connect()
        service._on_connection_made()

        service.cleanup()

        mock_protocol.disconnect.assert_called_once()
        mock_protocol.on_connection_made.disconnect.assert_called_once()
