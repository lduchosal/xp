"""State Monitor Service for terminal interface."""

import logging
from datetime import datetime
from typing import Dict, List

from psygnal import Signal

from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.term.connection_state import ConnectionState
from xp.models.term.module_state import ModuleState
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class StateMonitorService:
    """Service for module state monitoring in terminal interface.

    Wraps ConbusEventProtocol and ConsonModuleListConfig to provide
    high-level module state tracking for the TUI.

    Attributes:
        on_connection_state_changed: Signal emitted when connection state changes.
        on_module_list_updated: Signal emitted when module list refreshed from config.
        on_module_state_changed: Signal emitted when individual module state updates.
        on_module_error: Signal emitted when module error occurs.
        on_status_message: Signal emitted for status messages.
    """

    on_connection_state_changed: Signal = Signal(ConnectionState)
    on_module_list_updated: Signal = Signal(list)
    on_module_state_changed: Signal = Signal(ModuleState)
    on_module_error: Signal = Signal(str, str)
    on_status_message: Signal = Signal(str)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        conson_config: ConsonModuleListConfig,
    ) -> None:
        """Initialize the State Monitor service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
            conson_config: ConsonModuleListConfig for module configuration.
        """
        self.logger = logging.getLogger(__name__)
        self._conbus_protocol = conbus_protocol
        self._conson_config = conson_config
        self._connection_state = ConnectionState.DISCONNECTED
        self._state_machine = ConnectionState.create_state_machine()
        self._module_states: Dict[str, ModuleState] = {}

        # Connect to protocol signals
        self._connect_signals()

        # Initialize module states from config
        self._initialize_module_states()

    def _initialize_module_states(self) -> None:
        """Initialize module states from ConsonModuleListConfig."""
        for module_config in self._conson_config.root:
            # Map auto_report_status: PP → True, others → False
            auto_report = module_config.auto_report_status == "PP"

            module_state = ModuleState(
                name=module_config.name,
                serial_number=module_config.serial_number,
                module_type=module_config.module_type,
                outputs="",  # Empty initially
                auto_report=auto_report,
                error_status="OK",
                last_update=None,  # Not updated yet
            )
            self._module_states[module_config.serial_number] = module_state

    def _connect_signals(self) -> None:
        """Connect to protocol signals."""
        self._conbus_protocol.on_connection_made.connect(self._on_connection_made)
        self._conbus_protocol.on_connection_failed.connect(self._on_connection_failed)
        self._conbus_protocol.on_telegram_received.connect(self._on_telegram_received)
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

    @property
    def module_states(self) -> List[ModuleState]:
        """Get all module states.

        Returns:
            List of all module states.
        """
        return list(self._module_states.values())

    def connect(self) -> None:
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

    def disconnect(self) -> None:
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
            self.disconnect()
        else:
            self.connect()

    def refresh_all(self) -> None:
        """Refresh all module states.

        Force reload all module states from the system by querying status.
        """
        self.on_status_message.emit("Refreshing all module states...")
        # Query each module for status
        for module_state in self._module_states.values():
            self._query_module_status(module_state.serial_number)

    def _query_module_status(self, serial_number: str) -> None:
        """Query module status.

        Args:
            serial_number: Module serial number to query.
        """
        # TODO: Implement actual status query via protocol
        # For now, just emit status message
        self.logger.debug(f"Querying status for module {serial_number}")

    def _on_connection_made(self) -> None:
        """Handle connection made event."""
        if self._state_machine.transition("connected", ConnectionState.CONNECTED):
            self._connection_state = ConnectionState.CONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connected to {self.server_info}")

            # Emit initial module list
            self.on_module_list_updated.emit(self.module_states)

    def _on_connection_failed(self, failure: Exception) -> None:
        """Handle connection failed event.

        Args:
            failure: Exception that caused the failure.
        """
        if self._state_machine.transition("failed", ConnectionState.FAILED):
            self._connection_state = ConnectionState.FAILED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connection failed: {failure}")

    def _on_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Parse output states from telegram and update module state.

        Args:
            event: Telegram received event.
        """
        # Update last_update for the module that sent the telegram
        serial_number = event.serial_number
        if serial_number and serial_number in self._module_states:
            module_state = self._module_states[serial_number]
            module_state.last_update = datetime.now()
            self.on_module_state_changed.emit(module_state)
            self.logger.debug(f"Updated last_update for {serial_number}")

    def _on_timeout(self) -> None:
        """Handle timeout event."""
        self.on_status_message.emit("Connection timeout")

    def _on_failed(self, failure: Exception) -> None:
        """Handle protocol failure event.

        Args:
            failure: Exception that caused the failure.
        """
        if self._state_machine.transition("failed", ConnectionState.FAILED):
            self._connection_state = ConnectionState.FAILED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Protocol error: {failure}")

    def cleanup(self) -> None:
        """Clean up service resources."""
        self._disconnect_signals()
        self.logger.debug("StateMonitorService cleaned up")

    def __enter__(self) -> "StateMonitorService":
        """Context manager entry.

        Returns:
            Self for context manager.
        """
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type.
            exc_val: Exception value.
            exc_tb: Exception traceback.
        """
        self.cleanup()
