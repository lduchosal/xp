# Copyright (c) 2025 ldvchosal
"""Conbus Reverse Proxy Service for TCP relay with telegram monitoring.

This service implements a TCP reverse proxy that listens on port 10001 and forwards all
telegrams to the configured Conbus server while logging bidirectional traffic.
"""

import logging
import socket
import threading
import time

from xp.models import ConbusClientConfig
from xp.models.response import Response
from xp.utils.time_utils import local_now


class ReverseProxyError(Exception):
    """Raised when Conbus reverse proxy operations fail."""


class ReverseProxyService:
    """TCP reverse proxy for Conbus communications.

    Accepts client connections on port 10001 and forwards all telegrams
    to the target server configured in cli.yml. Monitors and logs all
    bidirectional traffic with timestamps.

    Attributes:
        logger: Logger instance for the service.
        listen_port: Port to listen on for client connections.
        server_socket: Main server socket for accepting connections.
        is_running: Flag indicating if proxy is running.
        active_connections: Dictionary of active connection information.
        connection_counter: Counter for connection IDs.
        cli_config: Conbus client configuration.
        target_ip: Target server IP address.
        target_port: Target server port number.

    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        listen_port: int,
    ) -> None:
        """Initialize the Conbus reverse proxy service.

        Args:
            cli_config: Conbus client configuration.
            listen_port: Port to listen on for client connections.

        """
        # Set up logging first
        self.logger = logging.getLogger(__name__)

        self.listen_port = listen_port
        self.server_socket: socket.socket | None = None
        self.is_running = False
        self.active_connections: dict[str, dict] = {}
        self.connection_counter = 0

        # Target server configuration
        self.cli_config = cli_config

    @property
    def target_ip(self) -> str:
        """Target server IP.

        Returns:
            Target server IP address.

        """
        return self.cli_config.conbus.ip

    @property
    def target_port(self) -> int:
        """Target server port.

        Returns:
            Target server port number.

        """
        return self.cli_config.conbus.port

    def start_proxy(self) -> Response:
        """Start the reverse proxy server.

        Returns:
            Response object with success status and proxy details.

        """
        if self.is_running:
            return Response(
                success=False, data=None, error="Reverse proxy is already running"
            )

        try:
            # Create TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to listen port on all interfaces: the proxy must accept
            # connections from external Conbus clients by design.
            self.server_socket.bind(("0.0.0.0", self.listen_port))  # noqa: S104
            self.server_socket.listen(5)  # Allow multiple connections in queue

            self.is_running = True
            self.logger.info("Reverse proxy started on port %s", self.listen_port)
            self.logger.info(
                "Forwarding to %s:%s",
                self.cli_config.conbus.ip,
                self.cli_config.conbus.port,
            )
            self.logger.info("Monitoring all traffic...")

            # Start accepting connections in background thread
            accept_thread = threading.Thread(
                target=self._accept_connections, daemon=True
            )
            accept_thread.start()

            return Response(
                success=True,
                data={
                    "listen_port": self.listen_port,
                    "target_ip": self.cli_config.conbus.ip,
                    "target_port": self.cli_config.conbus.port,
                    "message": "Reverse proxy started successfully",
                },
                error=None,
            )

        except Exception as e:
            self.logger.exception("Failed to start reverse proxy")
            return Response(
                success=False, data=None, error=f"Failed to start reverse proxy: {e}"
            )

    def stop_proxy(self) -> Response:
        """Stop the reverse proxy server.

        Returns:
            Response object with success status.

        """
        if not self.is_running:
            return Response(
                success=False, data=None, error="Reverse proxy is not running"
            )

        self.is_running = False

        # Close all active connections
        for conn_id, _conn_info in list(self.active_connections.items()):
            self._close_connection_pair(conn_id)

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.logger.info("Reverse proxy stopped")
            except Exception:
                self.logger.exception("Error closing server socket")

        return Response(
            success=True,
            data={"message": "Reverse proxy stopped successfully"},
            error=None,
        )

    def get_status(self) -> Response:
        """Get current proxy status and active connections.

        Returns:
            Response object with proxy status and connection details.

        """
        return Response(
            success=True,
            data={
                "running": self.is_running,
                "listen_port": self.listen_port,
                "target_ip": self.cli_config.conbus.ip,
                "target_port": self.cli_config.conbus.port,
                "active_connections": len(self.active_connections),
                "connections": {
                    conn_id: {
                        "client_address": info["client_address"],
                        "connected_at": info["connected_at"].isoformat(),
                        "bytes_relayed": info.get("bytes_relayed", 0),
                    }
                    for conn_id, info in self.active_connections.items()
                },
            },
            error=None,
        )

    def _accept_connections(self) -> None:
        """Accept and handle client connections."""
        while self.is_running:
            try:
                # Accept connection
                if self.server_socket is None:
                    break
                client_socket, client_address = self.server_socket.accept()

                # Generate connection ID
                self.connection_counter += 1
                conn_id = f"conn_{self.connection_counter}"

                self.logger.info(
                    "Client connected from %s [%s]", client_address, conn_id
                )

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address, conn_id),
                    daemon=True,
                )
                client_thread.start()

            except Exception:
                if self.is_running:
                    self.logger.exception("Error accepting connection")
                break

    def _handle_client(
        self, client_socket: socket.socket, client_address: tuple, conn_id: str
    ) -> None:
        """Handle individual client connection with server relay.

        Args:
            client_socket: Client socket connection.
            client_address: Client address tuple (ip, port).
            conn_id: Connection identifier.

        """
        try:
            # Connect to target server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(self.cli_config.conbus.timeout)
            server_socket.connect(
                (self.cli_config.conbus.ip, self.cli_config.conbus.port)
            )

            # Store connection info
            self.active_connections[conn_id] = {
                "client_socket": client_socket,
                "server_socket": server_socket,
                "client_address": client_address,
                "connected_at": local_now(),
                "bytes_relayed": 0,
            }

            self.logger.info(
                "Connected to target server %s:%s [%s]",
                self.cli_config.conbus.ip,
                self.cli_config.conbus.port,
                conn_id,
            )

            # Set timeouts for idle connections
            client_socket.settimeout(30.0)
            server_socket.settimeout(30.0)

            # Start bidirectional relay threads
            client_to_server_thread = threading.Thread(
                target=self._relay_data,
                args=(
                    client_socket,
                    server_socket,
                    "CLIENT→PROXY",
                    "PROXY→SERVER",
                    conn_id,
                ),
                daemon=True,
            )
            server_to_client_thread = threading.Thread(
                target=self._relay_data,
                args=(
                    server_socket,
                    client_socket,
                    "SERVER→PROXY",
                    "PROXY→CLIENT",
                    conn_id,
                ),
                daemon=True,
            )

            client_to_server_thread.start()
            server_to_client_thread.start()

            # Wait for either thread to finish (indicating connection closure)
            client_to_server_thread.join()
            server_to_client_thread.join()

        except TimeoutError:
            self.logger.info("Connection to target server timed out [%s]", conn_id)
        except Exception:
            self.logger.exception(
                "Error handling client %s [%s]", client_address, conn_id
            )
        finally:
            self._close_connection_pair(conn_id)

    def _relay_data(
        self,
        source_socket: socket.socket,
        dest_socket: socket.socket,
        source_label: str,
        dest_label: str,
        conn_id: str,
    ) -> None:
        """Relay data between sockets with telegram monitoring.

        Args:
            source_socket: Source socket to receive from.
            dest_socket: Destination socket to send to.
            source_label: Label for source in logs.
            dest_label: Label for destination in logs.
            conn_id: Connection identifier.

        """
        try:
            while self.is_running:
                # Receive data from source
                data = source_socket.recv(1024)
                if not data:
                    break

                # Decode and log telegram
                try:
                    message = data.decode("latin-1").strip()
                    if message:
                        self.logger.info("[%s] %s", source_label, message)

                        # Forward to destination
                        dest_socket.send(data)
                        self.logger.info("[%s] %s", dest_label, message)

                        # Update bytes relayed counter
                        if conn_id in self.active_connections:
                            self.active_connections[conn_id]["bytes_relayed"] += len(
                                data
                            )

                except UnicodeDecodeError:
                    # Handle binary data
                    self.logger.info(
                        "[%s] <binary data: %s bytes>", source_label, len(data)
                    )
                    dest_socket.send(data)
                    self.logger.info(
                        "[%s] <binary data: %s bytes>", dest_label, len(data)
                    )

                    if conn_id in self.active_connections:
                        self.active_connections[conn_id]["bytes_relayed"] += len(data)

        except TimeoutError:
            self.logger.debug("Socket timeout in relay [%s]", conn_id)
        except Exception:
            if self.is_running:
                self.logger.exception("Error in data relay [%s]", conn_id)

    def _close_connection_pair(self, conn_id: str) -> None:
        """Close both client and server sockets for a connection.

        Args:
            conn_id: Connection identifier.

        """
        if conn_id not in self.active_connections:
            return

        conn_info = self.active_connections[conn_id]

        # Close client socket
        try:
            if "client_socket" in conn_info:
                conn_info["client_socket"].close()
        except Exception:
            self.logger.exception("Error closing client socket [%s]", conn_id)

        # Close server socket
        try:
            if "server_socket" in conn_info:
                conn_info["server_socket"].close()
        except Exception:
            self.logger.exception("Error closing server socket [%s]", conn_id)

        # Log disconnection
        client_address = conn_info.get("client_address", "unknown")
        bytes_relayed = conn_info.get("bytes_relayed", 0)

        self.logger.info(
            "Client %s disconnected [%s] - %s bytes relayed",
            client_address,
            conn_id,
            bytes_relayed,
        )

        # Remove from active connections
        del self.active_connections[conn_id]

    @staticmethod
    def timestamp() -> str:
        """Generate timestamp string for logging.

        Returns:
            Timestamp string in HH:MM:SS,mmm format.

        """
        return local_now().strftime("%H:%M:%S,%f")[:-3]

    def run_blocking(self) -> None:
        """Run the proxy in blocking mode (for CLI usage).

        Raises:
            ReverseProxyError: If proxy fails to start.

        """
        result = self.start_proxy()
        if not result.success:
            raise ReverseProxyError(result.error)

        try:
            # Keep running until interrupted
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down")
            self.stop_proxy()
