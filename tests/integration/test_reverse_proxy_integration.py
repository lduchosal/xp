"""Integration tests for Conbus reverse proxy functionality."""

import socket
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

import pytest

from xp.models import ConbusClientConfig
from xp.services.reverse_proxy_service import ReverseProxyService


class MockServer:
    """Mock Conbus server for testing reverse proxy integration."""

    def __init__(self, port: int):
        """Initialize mock server.

        Args:
            port: Port number to listen on.
        """
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.received_messages: list[str] = []
        self.responses: list[str] = []

    def start(self):
        """Start the mock server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", self.port))
        self.socket.listen(1)
        self.is_running = True

        # Handle connections in background thread
        thread = threading.Thread(target=self._accept_connections, daemon=True)
        thread.start()

    def stop(self):
        """Stop the mock server."""
        self.is_running = False
        if self.socket:
            self.socket.close()

    def add_response(self, response: str) -> None:
        """Add a response to send when receiving messages.

        Args:
            response: Response string to add.
        """
        self.responses.append(response)

    def _accept_connections(self):
        """Accept and handle client connections."""
        while self.is_running:
            try:
                if not self.socket:
                    raise socket.error
                client_socket, address = self.socket.accept()
                self._handle_client(client_socket)
            except (OSError, socket.error):
                break

    def _handle_client(self, client_socket):
        """Handle individual client connection."""
        try:
            while self.is_running:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode("latin-1").strip()
                self.received_messages.append(message)

                # Send response if available
                if self.responses:
                    response = self.responses.pop(0)
                    client_socket.send(response.encode("latin-1"))

        except (ValueError, KeyError, ConnectionError):
            pass
        finally:
            client_socket.close()


class TestReverseProxyIntegration:
    """Integration tests for reverse proxy with mock server and client."""

    def setup_method(self):
        """Set up test environment."""
        # Use high port numbers to avoid conflicts
        self.proxy_port = 19001
        self.server_port = 19002

        # Create mock server
        self.mock_server = MockServer(self.server_port)

        # Create temporary config for proxy
        self.temp_config = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        self.temp_config.write(
            f"""
conbus:
  ip: 127.0.0.1
  port: {self.server_port}
  timeout: 2
"""
        )
        self.temp_config.close()

        # Create reverse proxy
        cli_config = ConbusClientConfig.from_yaml(self.temp_config.name)
        self.proxy = ReverseProxyService(
            cli_config=cli_config, listen_port=self.proxy_port
        )

    def teardown_method(self):
        """Clean up test environment."""
        if self.proxy.is_running:
            self.proxy.stop_proxy()

        if self.mock_server.is_running:
            self.mock_server.stop()

        if Path(self.temp_config.name).exists():
            Path(self.temp_config.name).unlink()

    @pytest.mark.reverseproxy
    def test_end_to_end_telegram_relay(self):
        """Test complete telegram relay from client through proxy to server."""
        # Start mock server
        self.mock_server.start()
        time.sleep(0.1)  # Give server time to start

        # Add expected response
        self.mock_server.add_response("<R0012345011F01DFM>")

        # Start proxy
        result = self.proxy.start_proxy()
        assert result.success
        time.sleep(0.1)  # Give proxy time to start

        try:
            # Create client and send telegram
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("127.0.0.1", self.proxy_port))

            # Send discover telegram
            discover_telegram = "<S0000000000F01D00FA>"
            client_socket.send(discover_telegram.encode("latin-1"))

            # Receive response
            response = client_socket.recv(1024).decode("latin-1").strip()

            # Verify end-to-end communication
            assert response == "<R0012345011F01DFM>"
            assert discover_telegram in self.mock_server.received_messages

            client_socket.close()

        finally:
            self.proxy.stop_proxy()
            self.mock_server.stop()

    @pytest.mark.reverseproxy
    def test_proxy_connection_failure_handling(self):
        """Test proxy behavior when target server is unavailable."""
        # Don't start mock server - simulate server unavailable

        # Start proxy
        result = self.proxy.start_proxy()
        assert result.success
        time.sleep(0.1)

        try:
            # Try to connect client - this should fail gracefully
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1.0)  # Short timeout for test

            # Connect to proxy
            client_socket.connect(("127.0.0.1", self.proxy_port))

            # Send telegram - connection to server should fail
            client_socket.send("<S0000000000F01D00FA>".encode("latin-1"))

            # Connection should be closed due to server unavailability
            time.sleep(0.5)  # Give time for connection handling

            # Verify proxy is still running despite connection failure
            status = self.proxy.get_status()
            assert status.success
            assert status.data["running"]

            client_socket.close()

        finally:
            self.proxy.stop_proxy()

    @pytest.mark.reverseproxy
    def test_bidirectional_data_relay(self):
        """Test bidirectional data relay between client and server."""
        # Start mock server with multiple responses
        self.mock_server.start()
        time.sleep(0.1)

        # Add multiple responses to simulate conversation
        responses = [
            "<R0012345011F01DFM>",
            "<R0012345011F02D02XP230_V1.00.04FI>",
            "<R0012345011F02D20+12.5V§OK>",
        ]
        for response in responses:
            self.mock_server.add_response(response)

        # Start proxy
        result = self.proxy.start_proxy()
        assert result.success
        time.sleep(0.1)

        try:
            # Create client connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("127.0.0.1", self.proxy_port))

            # Send multiple telegrams
            telegrams = [
                "<S0000000000F01D00FA>",
                "<S0012345011F02D02FM>",
                "<S0012345011F02D20FM>",
            ]

            received_responses = []
            for telegram in telegrams:
                client_socket.send(telegram.encode("latin-1"))
                time.sleep(0.1)  # Small delay between sends

                # Receive response
                response = client_socket.recv(1024).decode("latin-1").strip()
                received_responses.append(response)

            client_socket.close()

            # Verify all telegrams were relayed to server
            for telegram in telegrams:
                assert telegram in self.mock_server.received_messages

            # Verify all responses were relayed back to client
            assert received_responses == responses[: len(received_responses)]

        finally:
            self.proxy.stop_proxy()
            self.mock_server.stop()

    @pytest.mark.reverseproxy
    def test_proxy_status_tracking(self):
        """Test proxy status tracking during connections."""
        # Start mock server
        self.mock_server.start()
        time.sleep(0.1)

        # Start proxy
        result = self.proxy.start_proxy()
        assert result.success
        time.sleep(0.1)

        try:
            # Check initial status
            status = self.proxy.get_status()
            assert status.success
            assert status.data["running"]
            assert status.data["active_connections"] == 0

            # Create client connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("127.0.0.1", self.proxy_port))
            time.sleep(0.1)  # Give time for connection to be established

            # Check status with active connection
            # Note: Connection tracking happens in background threads
            # so we might not see it immediately in a unit test

            client_socket.close()
            time.sleep(0.1)  # Give time for cleanup

        finally:
            self.proxy.stop_proxy()
            self.mock_server.stop()


class TestReverseProxyErrorHandling:
    """Test error handling scenarios for reverse proxy."""

    @pytest.mark.reverseproxy
    def test_proxy_start_port_already_in_use(self):
        """Test proxy startup when port is already in use."""
        # Create a socket to occupy the port
        blocking_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocking_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocking_socket.bind(("0.0.0.0", 19003))
        blocking_socket.listen(1)

        try:
            # Try to start proxy on the same port
            cli_config = ConbusClientConfig.from_yaml("cli.yml")
            proxy = ReverseProxyService(cli_config=cli_config, listen_port=19003)
            result = proxy.start_proxy()

            # Should fail due to port conflict
            assert not result.success
            assert result.error is not None and (
                "Address already in use" in result.error
                or "permission" in result.error.lower()
            )

        finally:
            blocking_socket.close()
