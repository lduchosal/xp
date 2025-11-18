"""Protocol Monitor Service for terminal interface."""

import logging
from typing import Any, ItemsView, Optional

from psygnal import Signal
from twisted.python.failure import Failure

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.term.connection_state import ConnectionState
from xp.models.term.protocol_keys_config import ProtocolKeyConfig, ProtocolKeysConfig
from xp.models.term.telegram_display import TelegramDisplayEvent
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class ProtocolMonitorService:
    """Service for protocol monitoring in terminal interface.

    Wraps ConbusEventProtocol and provides high-level operations
    for the TUI without exposing protocol implementation details.

    Attributes:
        _conbus_protocol: Protocol instance for Conbus communication.
        _protocol_keys: Configuration for protocol keyboard shortcuts.
        connection_state: Current connection state (read-only property).
        server_info: Server connection info as "IP:port" (read-only property).
        on_connection_state_changed: Signal emitted when connection state changes.
        on_telegram_display: Signal emitted when telegram should be displayed.
        on_status_message: Signal emitted for status updates.
    """

    on_connection_state_changed: Signal = Signal(ConnectionState)
    on_telegram_display: Signal = Signal(TelegramDisplayEvent)
    on_status_message: Signal = Signal(str)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        protocol_keys: ProtocolKeysConfig,
    ) -> None:
        """Initialize the Protocol Monitor service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
            protocol_keys: Protocol keys configuration.
        """
        self.logger = logging.getLogger(__name__)
        self._conbus_protocol = conbus_protocol
        self._connection_state = ConnectionState.DISCONNECTED
        self._state_machine = ConnectionState.create_state_machine()
        self._protocol_keys = protocol_keys

        # Connect to protocol signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to protocol signals."""
        self._conbus_protocol.on_connection_made.connect(self._on_connection_made)
        self._conbus_protocol.on_connection_failed.connect(self._on_connection_failed)
        self._conbus_protocol.on_telegram_received.connect(self._on_telegram_received)
        self._conbus_protocol.on_telegram_sent.connect(self._on_telegram_sent)
        self._conbus_protocol.on_timeout.connect(self._on_timeout)
        self._conbus_protocol.on_failed.connect(self._on_failed)

    def _disconnect_signals(self) -> None:
        """Disconnect from protocol signals."""
        self._conbus_protocol.on_connection_made.disconnect(self._on_connection_made)
        self._conbus_protocol.on_connection_failed.disconnect(
            self._on_connection_failed
        )
        self._conbus_protocol.on_telegram_received.disconnect(
            self._on_telegram_received
        )
        self._conbus_protocol.on_telegram_sent.disconnect(self._on_telegram_sent)
        self._conbus_protocol.on_timeout.disconnect(self._on_timeout)
        self._conbus_protocol.on_failed.disconnect(self._on_failed)

    @property
    def connection_state(self) -> ConnectionState:
        """Get current connection state.

        Returns:
            Current connection state.
        """
        return self._connection_state

    @property
    def server_info(self) -> str:
        """Get server connection info (IP:port).

        Returns:
            Server address in format "IP:port".
        """
        return f"{self._conbus_protocol.cli_config.ip}:{self._conbus_protocol.cli_config.port}"

    def _connect(self) -> None:
        """Initiate connection to server."""
        if not self._state_machine.can_transition("connect"):
            self.logger.warning(
                f"Cannot connect: current state is {self._connection_state.value}"
            )
            return

        if self._state_machine.transition("connecting", ConnectionState.CONNECTING):
            self._connection_state = ConnectionState.CONNECTING
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connecting to {self.server_info}...")

        self._conbus_protocol.connect()

    def _disconnect(self) -> None:
        """Disconnect from server."""
        if not self._state_machine.can_transition("disconnect"):
            self.logger.warning(
                f"Cannot disconnect: current state is {self._connection_state.value}"
            )
            return

        if self._state_machine.transition(
            "disconnecting", ConnectionState.DISCONNECTING
        ):
            self._connection_state = ConnectionState.DISCONNECTING
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit("Disconnecting...")

        self._conbus_protocol.disconnect()

        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self._connection_state = ConnectionState.DISCONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit("Disconnected")

    def toggle_connection(self) -> None:
        """Toggle connection state between connected and disconnected.

        Disconnects if currently connected or connecting.
        Connects if currently disconnected or failed.
        """
        if self._connection_state in (
            ConnectionState.CONNECTED,
            ConnectionState.CONNECTING,
        ):
            self._disconnect()
        else:
            self._connect()

    def _send_telegram(self, name: str, telegram: str) -> None:
        """Send a raw telegram.

        Args:
            name: Display name for the telegram.
            telegram: Raw telegram string.
        """
        try:
            self._conbus_protocol.send_raw_telegram(telegram)
            self.on_status_message.emit(f"{name} sent.")
        except Exception as e:
            self.logger.error(f"Failed to send telegram: {e}")
            self.on_status_message.emit(f"Failed: {e}")

    def handle_key_press(self, key: str) -> bool:
        """Handle protocol key press.

        Args:
            key: Key that was pressed.

        Returns:
            True if key was handled, False otherwise.
        """
        if key in self._protocol_keys.protocol:
            key_config = self._protocol_keys.protocol[key]
            for telegram in key_config.telegrams:
                self._send_telegram(key_config.name, telegram)
            return True
        return False

    # Protocol signal handlers

    def _on_connection_made(self) -> None:
        """Handle connection established."""
        if self._state_machine.transition("connected", ConnectionState.CONNECTED):
            self._connection_state = ConnectionState.CONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connected to {self.server_info}")

    def _on_connection_failed(self, failure: Failure) -> None:
        """Handle connection failed.

        Args:
            failure: Twisted failure object with error details.
        """
        if self._state_machine.transition("disconnected", ConnectionState.DISCONNECTED):
            self._connection_state = ConnectionState.DISCONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(failure.getErrorMessage())

    def _on_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle telegram received.

        Args:
            event: Telegram received event with frame data.
        """
        display_event = TelegramDisplayEvent(direction="RX", telegram=event.frame)
        self.on_telegram_display.emit(display_event)

    def _on_telegram_sent(self, telegram: str) -> None:
        """Handle telegram sent.

        Args:
            telegram: Sent telegram string.
        """
        display_event = TelegramDisplayEvent(direction="TX", telegram=telegram)
        self.on_telegram_display.emit(display_event)

    def _on_timeout(self) -> None:
        """Handle timeout."""
        self.logger.debug("Timeout occurred (continuous monitoring)")

    def _on_failed(self, error: str) -> None:
        """Handle connection failed.

        Args:
            error: Error message describing the failure.
        """
        if self._state_machine.transition("failed", ConnectionState.FAILED):
            self._connection_state = ConnectionState.FAILED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Failed: {error}")

    def cleanup(self) -> None:
        """Clean up service resources."""
        self._disconnect_signals()
        if self._conbus_protocol.transport:
            self._disconnect()

    def get_keys(self) -> ItemsView[str, ProtocolKeyConfig]:
        """Get protocol key mappings.

        Returns:
            Dictionary items view of key to ProtocolKeyConfig mappings.
        """
        return self._protocol_keys.protocol.items()

    def __enter__(self) -> "ProtocolMonitorService":
        """Enter context manager.

        Returns:
            Self for context management.
        """
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[Any],
    ) -> None:
        """Exit context manager and clean up resources.

        Args:
            _exc_type: Exception type if any.
            _exc_val: Exception value if any.
            _exc_tb: Exception traceback if any.
        """
        self.cleanup()
