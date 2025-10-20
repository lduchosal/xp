"""Conbus Reverse Proxy Service for TCP relay with telegram monitoring.

This service implements a TCP reverse proxy that listens on port 10001 and forwards
all telegrams to the configured Conbus server while printing bidirectional traffic.
"""

import logging
import socket
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from xp.models import ConbusClientConfig
from xp.models.response import Response


class ReverseProxyError(Exception):
    """Raised when Conbus reverse proxy operations fail."""

    pass


class ReverseProxyService:
    """
    TCP reverse proxy for Conbus communications.

    Accepts client connections on port 10001 and forwards all telegrams
    to the target server configured in cli.yml. Monitors and prints all
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
    ):
        """Initialize the Conbus reverse proxy service.

        Args:
            cli_config: Conbus client configuration.
            listen_port: Port to listen on for client connections.
        """
        # Set up logging first
        self.logger = logging.getLogger(__name__)

        self.listen_port = listen_port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.active_connections: Dict[str, dict] = {}
        self.connection_counter = 0

        # Target server configuration
        self.cli_config = cli_config

    @property
    def target_ip(self) -> str:
        """Get target server IP.

        Returns:
            Target server IP address.
        """
        return self.cli_config.conbus.ip

    @property
    def target_port(self) -> int:
        """Get target server port.

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

            # Bind to listen port on all interfaces
            self.server_socket.bind(("0.0.0.0", self.listen_port))
            self.server_socket.listen(5)  # Allow multiple connections in queue

            self.is_running = True
            self.logger.info(f"Reverse proxy started on port {self.listen_port}")
            self.logger.info(
                f"Forwarding to {self.cli_config.conbus.ip}:{self.cli_config.conbus.port}"
            )

            # Print startup message
            print(f"Conbus Reverse Proxy started on port {self.listen_port}")
            print(
                f"Forwarding telegrams to {self.cli_config.conbus.ip}:{self.cli_config.conbus.port}"
            )
            print("Monitoring all traffic...\n")

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
            self.logger.error(f"Failed to start reverse proxy: {e}")
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
        for conn_id, conn_info in list(self.active_connections.items()):
            self._close_connection_pair(conn_id)

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.logger.info("Reverse proxy stopped")
                print("Reverse proxy stopped")
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")

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

                self.logger.info(f"Client connected from {client_address} [{conn_id}]")
                print(
                    f"{self.timestamp()} [CONNECTION] Client {client_address} connected [{conn_id}]"
                )

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address, conn_id),
                    daemon=True,
                )
                client_thread.start()

            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")
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
                "connected_at": datetime.now(),
                "bytes_relayed": 0,
            }

            self.logger.info(
                f"Connected to target server {self.cli_config.conbus.ip}:{self.cli_config.conbus.port} [{conn_id}]"
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

        except socket.timeout:
            self.logger.info(f"Connection to target server timed out [{conn_id}]")
            print(
                f"{self.timestamp()} [ERROR] Connection to target server timed out [{conn_id}]"
            )
        except Exception as e:
            self.logger.error(
                f"Error handling client {client_address}: {e} [{conn_id}]"
            )
            print(f"{self.timestamp()} [ERROR] Connection error: {e} [{conn_id}]")
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

                # Decode and print telegram
                try:
                    message = data.decode("latin-1").strip()
                    if message:
                        print(f"{self.timestamp()} [{source_label}] {message}")

                        # Forward to destination
                        dest_socket.send(data)
                        print(f"{self.timestamp()} [{dest_label}] {message}")

                        # Update bytes relayed counter
                        if conn_id in self.active_connections:
                            self.active_connections[conn_id]["bytes_relayed"] += len(
                                data
                            )

                except UnicodeDecodeError:
                    # Handle binary data
                    print(
                        f"{self.timestamp()} [{source_label}] <binary data: {len(data)} bytes>"
                    )
                    dest_socket.send(data)
                    print(
                        f"{self.timestamp()} [{dest_label}] <binary data: {len(data)} bytes>"
                    )

                    if conn_id in self.active_connections:
                        self.active_connections[conn_id]["bytes_relayed"] += len(data)

        except socket.timeout:
            self.logger.debug(f"Socket timeout in relay [{conn_id}]")
        except Exception as e:
            if self.is_running:
                self.logger.error(f"Error in data relay: {e} [{conn_id}]")

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
        except Exception as e:
            self.logger.error(f"Error closing client socket: {e} [{conn_id}]")

        # Close server socket
        try:
            if "server_socket" in conn_info:
                conn_info["server_socket"].close()
        except Exception as e:
            self.logger.error(f"Error closing server socket: {e} [{conn_id}]")

        # Log disconnection
        client_address = conn_info.get("client_address", "unknown")
        bytes_relayed = conn_info.get("bytes_relayed", 0)

        self.logger.info(
            f"Client {client_address} disconnected [{conn_id}] - {bytes_relayed} bytes relayed"
        )
        print(
            f"{self.timestamp()} [DISCONNECTION] "
            f"Client {client_address} "
            f"disconnected [{conn_id}] - "
            f"{bytes_relayed} bytes relayed"
        )

        # Remove from active connections
        del self.active_connections[conn_id]

    @staticmethod
    def timestamp() -> str:
        """Generate timestamp string for logging.

        Returns:
            Timestamp string in HH:MM:SS,mmm format.
        """
        return datetime.now().strftime("%H:%M:%S,%f")[:-3]

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
            print(f"\n{self.timestamp()} [SHUTDOWN] Received interrupt signal")
            self.stop_proxy()
