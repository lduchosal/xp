# Copyright (c) 2025 ldvchosal
"""Tests for ClientBufferManager."""

import queue
import socket
import threading
import time
from unittest.mock import Mock

from xp.services.server.client_buffer_manager import ClientBufferManager

BROADCAST_COUNT = 3
MESSAGE_COUNT = 10
CLIENT_COUNT = 3


class TestClientBufferManagerInit:
    """Test ClientBufferManager initialization."""

    def test_init(self) -> None:
        """Test initialization creates empty buffer dictionary."""
        manager = ClientBufferManager()
        # No public API exposes the buffer dict; checking initial state
        assert manager._buffers == {}  # noqa: SLF001


class TestClientBufferManagerRegistration:
    """Test client registration and unregistration."""

    def test_register_client_creates_queue(self) -> None:
        """Test registering a client creates a new queue."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)

        client_queue = manager.register_client(mock_socket)

        assert isinstance(client_queue, queue.Queue)
        assert manager.get_queue(mock_socket) is not None

    def test_register_client_returns_queue(self) -> None:
        """Test registering a client returns the created queue."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)

        returned_queue = manager.register_client(mock_socket)
        stored_queue = manager.get_queue(mock_socket)

        assert returned_queue is stored_queue

    def test_register_multiple_clients(self) -> None:
        """Test registering multiple clients creates separate queues."""
        manager = ClientBufferManager()
        mock_socket1 = Mock(spec=socket.socket)
        mock_socket2 = Mock(spec=socket.socket)

        queue1 = manager.register_client(mock_socket1)
        queue2 = manager.register_client(mock_socket2)

        assert queue1 is not queue2
        assert manager.get_queue(mock_socket1) is queue1
        assert manager.get_queue(mock_socket2) is queue2

    def test_unregister_client_removes_queue(self) -> None:
        """Test unregistering a client removes its queue."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        manager.register_client(mock_socket)

        manager.unregister_client(mock_socket)

        assert manager.get_queue(mock_socket) is None

    def test_unregister_nonexistent_client(self) -> None:
        """Test unregistering a non-existent client does not raise error."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)

        manager.unregister_client(mock_socket)  # Should not raise

    def test_unregister_client_twice(self) -> None:
        """Test unregistering a client twice does not raise error."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        manager.register_client(mock_socket)

        manager.unregister_client(mock_socket)
        manager.unregister_client(mock_socket)  # Should not raise


class TestClientBufferManagerBroadcast:
    """Test telegram broadcasting."""

    def test_broadcast_to_single_client(self) -> None:
        """Test broadcasting a telegram to a single client."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        client_queue = manager.register_client(mock_socket)

        manager.broadcast("test telegram")

        assert client_queue.qsize() == 1
        assert client_queue.get_nowait() == "test telegram"

    def test_broadcast_to_multiple_clients(self) -> None:
        """Test broadcasting a telegram to multiple clients."""
        manager = ClientBufferManager()
        mock_socket1 = Mock(spec=socket.socket)
        mock_socket2 = Mock(spec=socket.socket)
        mock_socket3 = Mock(spec=socket.socket)

        queue1 = manager.register_client(mock_socket1)
        queue2 = manager.register_client(mock_socket2)
        queue3 = manager.register_client(mock_socket3)

        manager.broadcast("broadcast telegram")

        assert queue1.get_nowait() == "broadcast telegram"
        assert queue2.get_nowait() == "broadcast telegram"
        assert queue3.get_nowait() == "broadcast telegram"

    def test_broadcast_to_no_clients(self) -> None:
        """Test broadcasting when no clients are registered."""
        manager = ClientBufferManager()

        manager.broadcast("telegram")  # Should not raise

    def test_broadcast_multiple_telegrams(self) -> None:
        """Test broadcasting multiple telegrams to clients."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        client_queue = manager.register_client(mock_socket)

        manager.broadcast("telegram1")
        manager.broadcast("telegram2")
        manager.broadcast("telegram3")

        assert client_queue.qsize() == BROADCAST_COUNT
        assert client_queue.get_nowait() == "telegram1"
        assert client_queue.get_nowait() == "telegram2"
        assert client_queue.get_nowait() == "telegram3"

    def test_broadcast_after_client_unregistered(self) -> None:
        """Test broadcasting after a client is unregistered."""
        manager = ClientBufferManager()
        mock_socket1 = Mock(spec=socket.socket)
        mock_socket2 = Mock(spec=socket.socket)

        queue1 = manager.register_client(mock_socket1)
        queue2 = manager.register_client(mock_socket2)

        manager.unregister_client(mock_socket1)
        manager.broadcast("telegram")

        assert queue1.empty()  # Unregistered client should not receive
        assert queue2.get_nowait() == "telegram"


class TestClientBufferManagerGetQueue:
    """Test queue retrieval."""

    def test_get_queue_for_registered_client(self) -> None:
        """Test getting queue for a registered client."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        registered_queue = manager.register_client(mock_socket)

        retrieved_queue = manager.get_queue(mock_socket)

        assert retrieved_queue is registered_queue

    def test_get_queue_for_unregistered_client(self) -> None:
        """Test getting queue for an unregistered client returns None."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)

        retrieved_queue = manager.get_queue(mock_socket)

        assert retrieved_queue is None

    def test_get_queue_after_unregister(self) -> None:
        """Test getting queue after client is unregistered returns None."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        manager.register_client(mock_socket)
        manager.unregister_client(mock_socket)

        retrieved_queue = manager.get_queue(mock_socket)

        assert retrieved_queue is None


class TestClientBufferManagerThreadSafety:
    """Test thread safety of ClientBufferManager."""

    def test_concurrent_registration(self) -> None:
        """Test concurrent client registrations are thread-safe."""
        manager = ClientBufferManager()
        sockets = [Mock(spec=socket.socket) for _ in range(MESSAGE_COUNT)]
        threads = []

        def register_client(sock: socket.socket) -> None:
            """Register a client socket.

            Args:
                sock: Socket to register.

            """
            manager.register_client(sock)

        for sock in sockets:
            thread = threading.Thread(target=register_client, args=(sock,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert all(manager.get_queue(sock) is not None for sock in sockets)

    def test_concurrent_broadcast(self) -> None:
        """Test concurrent broadcasts are thread-safe."""
        manager = ClientBufferManager()
        mock_socket = Mock(spec=socket.socket)
        client_queue = manager.register_client(mock_socket)
        threads = []

        def broadcast_telegram(msg: str) -> None:
            """Broadcast a telegram message.

            Args:
                msg: Message to broadcast.

            """
            manager.broadcast(msg)

        for i in range(MESSAGE_COUNT):
            thread = threading.Thread(target=broadcast_telegram, args=(f"msg{i}",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert client_queue.qsize() == MESSAGE_COUNT

    def test_concurrent_register_and_broadcast(self) -> None:
        """Test concurrent registration and broadcasting are thread-safe."""
        manager = ClientBufferManager()
        results = []

        def register_and_receive(_sock_id: int) -> None:
            """Register client and receive messages.

            Args:
                _sock_id: Socket identifier (unused).

            """
            sock = Mock(spec=socket.socket)
            client_queue = manager.register_client(sock)
            time.sleep(0.01)  # Small delay to ensure broadcasts happen
            received = []
            while not client_queue.empty():
                try:
                    received.append(client_queue.get_nowait())
                except queue.Empty:
                    break
            results.append(len(received))

        def broadcast_messages() -> None:
            """Broadcast multiple messages."""
            for i in range(5):
                manager.broadcast(f"msg{i}")
                time.sleep(0.005)

        # Start broadcast thread
        broadcast_thread = threading.Thread(target=broadcast_messages)
        broadcast_thread.start()

        # Start registration threads
        register_threads = []
        for i in range(CLIENT_COUNT):
            thread = threading.Thread(target=register_and_receive, args=(i,))
            register_threads.append(thread)
            thread.start()

        broadcast_thread.join()
        for thread in register_threads:
            thread.join()

        # Each client should receive some messages
        # The exact count depends on timing, but none should crash
        assert len(results) == CLIENT_COUNT

    def test_concurrent_unregister_and_broadcast(self) -> None:
        """Test concurrent unregistration and broadcasting are thread-safe."""
        manager = ClientBufferManager()
        sockets = [Mock(spec=socket.socket) for _ in range(5)]
        for sock in sockets:
            manager.register_client(sock)

        def unregister_clients() -> None:
            """Unregister all clients."""
            for sock in sockets:
                manager.unregister_client(sock)
                time.sleep(0.01)

        def broadcast_messages() -> None:
            """Broadcast messages continuously."""
            for i in range(10):
                manager.broadcast(f"msg{i}")
                time.sleep(0.005)

        unregister_thread = threading.Thread(target=unregister_clients)
        broadcast_thread = threading.Thread(target=broadcast_messages)

        broadcast_thread.start()
        unregister_thread.start()

        broadcast_thread.join()
        unregister_thread.join()

        # Should complete without exceptions
        assert all(manager.get_queue(sock) is None for sock in sockets)
