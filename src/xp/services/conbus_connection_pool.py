"""Connection pooling implementation for Conbus TCP connections.

This module provides a singleton connection pool for managing TCP socket connections
to Conbus servers with automatic lifecycle management, health checking, and reconnection.
"""

import threading
import socket
import logging
import time
from contextlib import suppress
from typing import Optional, Any

from ..models import ConbusClientConfig


class ConbusSocketConnectionManager:
    """Connection manager for TCP socket connections to Conbus servers"""

    def __init__(self, host: str, port: int, timeout: float):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def create(self) -> socket.socket:
        """Create and configure a new TCP socket connection"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        self.logger.info(
            f"Created new connection to {self.host}:{self.port} (timeout: {self.timeout})"
        )
        return sock

    def dispose(self, connection: socket.socket) -> None:
        """Close and cleanup socket connection"""
        try:
            connection.close()
            self.logger.info("Disposed socket connection")
        except Exception as e:
            self.logger.warning(f"Error disposing connection: {e}")

    @staticmethod
    def check_aliveness(connection: socket.socket) -> bool:
        """Verify if connection is still alive"""
        try:
            # Use socket error checking rather than sending empty data
            # to avoid potential protocol issues
            error = connection.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            return error == 0
        except (socket.error, OSError):
            return False


class ConbusConnectionPool:
    """Singleton connection pool for Conbus TCP connections"""

    _instance: Optional["ConbusConnectionPool"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConbusConnectionPool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._config: Optional[ConbusClientConfig] = None
        self._connection: Optional[socket.socket] = None
        self._current_connection: Optional[socket.socket] = None
        self._connection_manager: Optional[ConbusSocketConnectionManager] = None
        self._connection_created_at: Optional[float] = None
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.idle_timeout = 21600  # 6 hours
        self.max_lifetime = 21600  # 6 hours

    def initialize(self, config: ConbusClientConfig) -> None:
        """Initialize the connection pool with configuration"""
        if self._config is not None:
            self.logger.info("Connection pool already initialized")
            return

        self._config = config
        self._connection_manager = ConbusSocketConnectionManager(
            config.ip, config.port, config.timeout
        )

        self.logger.info(f"Initialized connection pool for {config.ip}:{config.port}")

    def _is_connection_expired(self) -> bool:
        """Check if the current connection has expired"""
        if self._connection_created_at is None:
            return True

        age = time.time() - self._connection_created_at
        return age > self.max_lifetime

    def _is_connection_alive(self) -> bool:
        """Check if connection is still alive"""
        if self._connection is None or self._connection_manager is None:
            return False

        return self._connection_manager.check_aliveness(self._connection)

    def acquire_connection(self) -> socket.socket:
        """Acquire a connection from the pool"""
        if self._connection_manager is None:
            raise RuntimeError("Connection pool not initialized")

        with self._lock:
            # Check if we need a new connection
            if (
                self._connection is None
                or self._is_connection_expired()
                or not self._is_connection_alive()
            ):

                # Close existing connection if any
                if self._connection:
                    self._connection_manager.dispose(self._connection)
                    self._connection = None

                # Create new connection
                self._connection = self._connection_manager.create()
                self._connection_created_at = time.time()
                self.logger.debug("Created new connection")

            self.logger.debug("Acquired connection from pool")
            return self._connection

    # noinspection PyUnusedLocal
    def release_connection(self, connection: socket.socket) -> None:
        """Release a connection back to the pool (no-op for single connection pool)"""
        self.logger.debug("Released connection back to pool")
        # For single connection pool, we just log but don't actually close the connection

    def __enter__(self) -> socket.socket:
        """Context manager entry - acquire connection"""
        self._current_connection = self.acquire_connection()
        return self._current_connection

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit - release connection"""
        if hasattr(self, "_current_connection") and self._current_connection:
            self.release_connection(self._current_connection)
            self._current_connection = None

    @classmethod
    def get_instance(cls) -> "ConbusConnectionPool":
        """Get the singleton instance"""
        return cls()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing"""
        with cls._lock:
            if cls._instance:
                # Clean up existing connection
                if hasattr(cls._instance, "_connection") and cls._instance._connection:
                    with suppress(Exception):
                        cls._instance._connection.close()
            cls._instance = None

    def close(self) -> None:
        """Close the connection pool and cleanup resources"""
        with self._lock:
            if self._connection and self._connection_manager is not None:
                try:
                    self._connection_manager.dispose(self._connection)
                    self.logger.info("Connection pool closed")
                except Exception as e:
                    self.logger.error(f"Error closing connection pool: {e}")
                finally:
                    self._connection = None
                    self._connection_created_at = None
