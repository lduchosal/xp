# Copyright (c) 2025 ldvchosal
"""Unit tests for ReverseProxyService."""

import socket
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from xp.models import ConbusClientConfig
from xp.services.reverse_proxy_service import (
    ReverseProxyError,
    ReverseProxyService,
)

DEFAULT_TARGET_PORT = 10001
LISTEN_PORT = 10003
BYTES_RELAYED = 1024
TIMESTAMP_LENGTH = 12


class TestReverseProxyService:
    """Test cases for ReverseProxyService."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as temp_config:
            temp_config.write("""
conbus:
  ip: 192.168.1.100
  port: 10002
  timeout: 5.0
""")
        self.temp_config_name = temp_config.name

        cli_config = ConbusClientConfig.from_yaml(self.temp_config_name)
        self.service = ReverseProxyService(
            cli_config=cli_config, listen_port=LISTEN_PORT
        )

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        if self.service.is_running:
            self.service.stop_proxy()

        # Clean up temp file
        if Path(self.temp_config_name).exists():
            Path(self.temp_config_name).unlink()

    def test_init_with_defaults(self) -> None:
        """Test service initialization with default values."""
        cli_config = ConbusClientConfig.from_yaml("cli.yml")
        service = ReverseProxyService(
            cli_config=cli_config, listen_port=DEFAULT_TARGET_PORT
        )

        assert service.listen_port == DEFAULT_TARGET_PORT
        assert not service.is_running
        assert service.active_connections == {}
        assert service.connection_counter == 0

    def test_load_config_invalid_yaml(self) -> None:
        """Test configuration loading with invalid YAML."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as temp_invalid:
            temp_invalid.write("invalid: yaml: content: [")

        try:
            cli_config = ConbusClientConfig.from_yaml(temp_invalid.name)
            service = ReverseProxyService(
                cli_config=cli_config, listen_port=DEFAULT_TARGET_PORT
            )
            # Should use defaults when config is invalid
            assert service.target_ip == "192.168.1.100"
            assert service.target_port == DEFAULT_TARGET_PORT
        finally:
            Path(temp_invalid.name).unlink()

    @patch("socket.socket")
    def test_start_proxy_success(self, mock_socket_class: Mock) -> None:
        """Test successful proxy startup."""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        result = self.service.start_proxy()

        assert result.success
        assert self.service.is_running
        assert "Reverse proxy started successfully" in result.data["message"]
        assert result.data["listen_port"] == LISTEN_PORT

        # Verify socket setup
        mock_socket.setsockopt.assert_called_with(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        # Asserts the proxy binds all interfaces, mirroring the service code
        mock_socket.bind.assert_called_with(("0.0.0.0", LISTEN_PORT))  # noqa: S104
        mock_socket.listen.assert_called_with(5)

    def test_start_proxy_already_running(self) -> None:
        """Test starting proxy when already running."""
        self.service.is_running = True

        result = self.service.start_proxy()

        assert not result.success
        assert result.error is not None
        assert "already running" in result.error

    @patch("socket.socket")
    def test_start_proxy_socket_error(self, mock_socket_class: Mock) -> None:
        """Test proxy startup with socket error."""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_socket.bind.side_effect = OSError("Address already in use")

        result = self.service.start_proxy()

        assert not result.success
        assert result.error is not None
        assert "Address already in use" in result.error
        assert not self.service.is_running

    def test_stop_proxy_not_running(self) -> None:
        """Test stopping proxy when not running."""
        result = self.service.stop_proxy()

        assert not result.success
        assert result.error is not None
        assert "not running" in result.error

    def test_get_status_not_running(self) -> None:
        """Test status when proxy is not running."""
        result = self.service.get_status()

        assert result.success
        data = result.data
        assert not data["running"]
        assert data["listen_port"] == LISTEN_PORT
        assert data["active_connections"] == 0
        assert data["connections"] == {}

    def test_get_status_with_connections(self) -> None:
        """Test status with active connections."""
        # Mock some active connections
        self.service.is_running = True
        mock_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.service.active_connections = {
            "conn_1": {
                "client_address": ("192.168.1.50", 12345),
                "connected_at": mock_time,
                "bytes_relayed": BYTES_RELAYED,
            }
        }

        result = self.service.get_status()

        assert result.success
        data = result.data
        assert data["running"]
        assert data["active_connections"] == 1
        assert "conn_1" in data["connections"]
        assert data["connections"]["conn_1"]["client_address"] == (
            "192.168.1.50",
            12345,
        )
        assert data["connections"]["conn_1"]["bytes_relayed"] == BYTES_RELAYED

    def test_timestamp_format(self) -> None:
        """Test timestamp format generation."""
        timestamp = self.service.timestamp()

        # Should be in format HH:MM:SS,mmm
        assert len(timestamp) == TIMESTAMP_LENGTH
        assert timestamp[2] == ":"
        assert timestamp[5] == ":"
        assert timestamp[8] == ","

    def test_close_connection_pair(self) -> None:
        """Test closing connection pair."""
        # Mock connection info
        mock_client_socket = Mock()
        mock_server_socket = Mock()

        conn_id = "test_conn"
        self.service.active_connections[conn_id] = {
            "client_socket": mock_client_socket,
            "server_socket": mock_server_socket,
            "client_address": ("192.168.1.50", 12345),
            "bytes_relayed": 512,
        }

        # No public API closes a single connection pair
        self.service._close_connection_pair(conn_id)  # noqa: SLF001

        # Verify sockets were closed
        mock_client_socket.close.assert_called_once()
        mock_server_socket.close.assert_called_once()

        # Verify connection was removed
        assert conn_id not in self.service.active_connections

    def test_close_connection_pair_nonexistent(self) -> None:
        """Test closing non-existent connection pair."""
        # Should not raise exception
        # No public API closes a single connection pair
        self.service._close_connection_pair("nonexistent")  # noqa: SLF001
        assert len(self.service.active_connections) == 0

    def test_close_connection_pair_socket_error(self) -> None:
        """Test closing connection pair with socket errors."""
        # Mock connection info with sockets that raise exceptions
        mock_client_socket = Mock()
        mock_server_socket = Mock()
        mock_client_socket.close.side_effect = OSError("Socket error")
        mock_server_socket.close.side_effect = OSError("Socket error")

        conn_id = "test_conn"
        self.service.active_connections[conn_id] = {
            "client_socket": mock_client_socket,
            "server_socket": mock_server_socket,
            "client_address": ("192.168.1.50", 12345),
            "bytes_relayed": 0,
        }

        # Should not raise exception despite socket errors
        # No public API closes a single connection pair
        self.service._close_connection_pair(conn_id)  # noqa: SLF001

        # Connection should still be removed
        assert conn_id not in self.service.active_connections


class TestReverseProxyServiceIntegration:
    """Integration tests for ReverseProxyService."""

    def setup_method(self) -> None:
        """Set up integration test fixtures."""
        # Use a high port number to avoid conflicts
        self.listen_port = 19999
        self.target_port = 19998

        # Create temporary config
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as temp_config:
            temp_config.write(f"""
conbus:
  ip: 127.0.0.1
  port: {self.target_port}
  timeout: 2
""")
        self.temp_config_name = temp_config.name

        cli_config = ConbusClientConfig.from_yaml(self.temp_config_name)
        self.service = ReverseProxyService(
            cli_config=cli_config, listen_port=self.listen_port
        )

    def teardown_method(self) -> None:
        """Clean up integration test fixtures."""
        if self.service.is_running:
            self.service.stop_proxy()

        if Path(self.temp_config_name).exists():
            Path(self.temp_config_name).unlink()

    def test_proxy_lifecycle(self) -> None:
        """Test complete proxy lifecycle: start, status, stop."""
        # Start proxy
        with patch("threading.Thread"):
            result = self.service.start_proxy()
            assert result.success
            assert self.service.is_running

        # Check status
        status_result = self.service.get_status()
        assert status_result.success
        assert status_result.data["running"]
        assert status_result.data["listen_port"] == self.listen_port

        # Stop proxy
        stop_result = self.service.stop_proxy()
        assert stop_result.success
        assert not self.service.is_running

    def test_error_handling_start_failure(self) -> None:
        """Test error handling when start_proxy fails."""
        with patch.object(self.service, "start_proxy") as mock_start:
            mock_start.return_value.success = False
            mock_start.return_value.error = "Test error"

            with pytest.raises(ReverseProxyError, match="Test error"):
                self.service.run_blocking()
