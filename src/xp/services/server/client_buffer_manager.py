"""
Client buffer manager for broadcasting telegrams to connected clients.

This module provides thread-safe management of per-client telegram queues, enabling
broadcast of telegrams from device services to all connected clients.
"""

import queue
import socket
import threading
from typing import Dict, Optional


class ClientBufferManager:
    """
    Thread-safe manager for client telegram queues.

    Manages individual queues for each connected client, providing thread-safe
    operations for client registration, unregistration, and telegram broadcasting.
    """

    def __init__(self) -> None:
        """Initialize the client buffer manager."""
        self._buffers: Dict[socket.socket, queue.Queue[str]] = {}
        self._lock = threading.Lock()

    def register_client(self, client_socket: socket.socket) -> queue.Queue[str]:
        """
        Register a new client and create its telegram queue.

        Args:
            client_socket: The socket of the connecting client.

        Returns:
            The newly created queue for this client.
        """
        with self._lock:
            client_queue: queue.Queue[str] = queue.Queue()
            self._buffers[client_socket] = client_queue
            return client_queue

    def unregister_client(self, client_socket: socket.socket) -> None:
        """
        Unregister a client and remove its telegram queue.

        Args:
            client_socket: The socket of the disconnecting client.
        """
        with self._lock:
            self._buffers.pop(client_socket, None)

    def broadcast(self, telegram: str) -> None:
        """
        Broadcast a telegram to all connected clients.

        Args:
            telegram: The telegram string to broadcast.
        """
        with self._lock:
            for client_queue in self._buffers.values():
                client_queue.put(telegram)

    def get_queue(self, client_socket: socket.socket) -> Optional[queue.Queue[str]]:
        """
        Retrieve the queue for a specific client.

        Args:
            client_socket: The socket of the client.

        Returns:
            The client's queue if registered, None otherwise.
        """
        with self._lock:
            return self._buffers.get(client_socket)
