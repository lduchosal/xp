# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusEventProtocol."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from xp.models import ConbusClientConfig
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

DEFAULT_TIMEOUT_SECONDS = 5.0


class TestConbusEventProtocol:
    """Unit tests for ConbusEventProtocol functionality."""

    @pytest.fixture
    def mock_reactor(self) -> Mock:
        """Create a mock reactor.

        Returns:
            A mock reactor.

        """
        reactor = Mock()
        reactor.connectTCP = Mock()
        reactor.running = False
        return reactor

    @pytest.fixture
    def mock_cli_config(self) -> Mock:
        """Create a mock CLI config.

        Returns:
            A mock CLI config.

        """
        config = Mock(spec=ConbusClientConfig)
        config.conbus = Mock()
        config.conbus.ip = "192.168.1.100"
        config.conbus.port = 10001
        config.conbus.timeout = DEFAULT_TIMEOUT_SECONDS
        return config

    @pytest.fixture
    def mock_telegram_service(self) -> Mock:
        """Create a mock telegram service.

        Returns:
            A mock telegram service.

        """
        return Mock()

    @pytest.fixture
    def protocol(
        self, mock_cli_config: Mock, mock_reactor: Mock, mock_telegram_service: Mock
    ) -> ConbusEventProtocol:
        """Create protocol instance with mocks.

        Returns:
            Protocol instance with mocks.

        """
        return ConbusEventProtocol(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            telegram_service=mock_telegram_service,
        )

    def test_protocol_initialization(
        self, protocol: ConbusEventProtocol, mock_cli_config: Mock, mock_reactor: Mock
    ) -> None:
        """Test protocol can be initialized with required dependencies."""
        assert protocol.buffer == b""
        # No public accessor exposes the injected reactor
        assert protocol._reactor == mock_reactor  # noqa: SLF001
        assert protocol.cli_config == mock_cli_config.conbus
        assert protocol.timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_connect_without_running_event_loop(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test connect() works without running asyncio event loop."""
        # Call connect - should not raise exception
        protocol.connect()

        # Verify connectTCP was called with correct parameters
        mock_reactor.connectTCP.assert_called_once_with(
            "192.168.1.100", 10001, protocol
        )

    @pytest.mark.anyio(backends=["asyncio"])
    async def test_connect_with_running_event_loop(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test connect() auto-detects and sets running asyncio event loop."""
        with patch.object(protocol, "set_event_loop") as mock_set_event_loop:
            # Call connect within async context (event loop is running)
            protocol.connect()

            # Verify set_event_loop was called with the running event loop
            mock_set_event_loop.assert_called_once()
            call_args = mock_set_event_loop.call_args[0][0]
            assert isinstance(call_args, asyncio.AbstractEventLoop)

            # Verify connectTCP was still called
            mock_reactor.connectTCP.assert_called_once_with(
                "192.168.1.100", 10001, protocol
            )

    def test_set_event_loop(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test set_event_loop properly configures reactor."""
        # Create a real event loop
        loop = asyncio.new_event_loop()

        try:
            # Mock reactor attributes; the name mirrors twisted's private
            # AsyncioSelectorReactor._asyncioEventloop attribute
            mock_reactor._asyncioEventloop = None  # noqa: SLF001
            mock_reactor.running = False
            mock_reactor.startRunning = Mock()

            protocol.set_event_loop(loop)

            # Verify reactor was configured
            assert mock_reactor._asyncioEventloop == loop  # noqa: SLF001
            assert mock_reactor.running is True
            mock_reactor.startRunning.assert_called_once()
        finally:
            loop.close()

    def test_set_event_loop_without_start_running_method(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test set_event_loop works even if reactor lacks startRunning method."""
        # Create a real event loop
        loop = asyncio.new_event_loop()

        try:
            # Mock reactor attributes (no startRunning method); the name
            # mirrors twisted's private _asyncioEventloop attribute
            mock_reactor._asyncioEventloop = None  # noqa: SLF001
            mock_reactor.running = False
            # Don't add startRunning method

            protocol.set_event_loop(loop)

            # Verify reactor was configured
            assert mock_reactor._asyncioEventloop == loop  # noqa: SLF001
            assert mock_reactor.running is True
        finally:
            loop.close()

    def test_disconnect(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test disconnect calls reactor.disconnectAll."""
        protocol.disconnect()

        mock_reactor.disconnectAll.assert_called_once()

    def test_stop_reactor_when_running(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test stop_reactor stops the reactor if it's running."""
        mock_reactor.running = True
        mock_reactor.stop = Mock()

        protocol.stop_reactor()

        mock_reactor.stop.assert_called_once()

    def test_stop_reactor_when_not_running(
        self, protocol: ConbusEventProtocol, mock_reactor: Mock
    ) -> None:
        """Test stop_reactor does nothing if reactor is not running."""
        mock_reactor.running = False
        mock_reactor.stop = Mock()

        protocol.stop_reactor()

        mock_reactor.stop.assert_not_called()

    def test_send_raw_telegram(self, protocol: ConbusEventProtocol) -> None:
        """Test send_raw_telegram queues telegram."""
        with patch.object(protocol, "call_later") as mock_call_later:
            protocol.send_raw_telegram("E02L01I08M")

            # Verify telegram was queued
            assert not protocol.telegram_queue.empty()
            telegram = protocol.telegram_queue.get_nowait()
            assert telegram == b"E02L01I08M"

            # Verify queue manager was scheduled
            mock_call_later.assert_called_once()
