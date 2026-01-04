"""HomeKit Service for terminal interface."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from psygnal import Signal

from xp.models.config.conson_module_config import ConsonModuleListConfig
from xp.models.homekit.homekit_config import HomekitAccessoryConfig, HomekitConfig
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.module_type_code import ModuleTypeCode
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.models.term.accessory_state import AccessoryState
from xp.models.term.connection_state import ConnectionState
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_output_service import TelegramOutputService
from xp.services.telegram.telegram_service import TelegramService
from xp.services.term.homekit_accessory_driver import HomekitAccessoryDriver


class HomekitService:
    """
    Service for HomeKit accessory monitoring in terminal interface.

    Wraps ConbusEventProtocol, HomekitConfig, and ConsonModuleListConfig to provide
    high-level accessory state tracking for the TUI.

    Attributes:
        on_connection_state_changed: Signal emitted when connection state changes.
        on_room_list_updated: Signal emitted when accessory list refreshed from config.
        on_module_state_changed: Signal emitted when individual accessory state updates.
        on_module_error: Signal emitted when module error occurs.
        on_status_message: Signal emitted for status messages.
        connection_state: Property returning current connection state.
        server_info: Property returning server connection info (IP:port).
        accessory_states: Property returning list of all accessory states.
    """

    on_connection_state_changed: Signal = Signal(ConnectionState)
    on_room_list_updated: Signal = Signal(list)
    on_module_state_changed: Signal = Signal(AccessoryState)
    on_module_error: Signal = Signal(str, str)
    on_status_message: Signal = Signal(str)

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        homekit_config: HomekitConfig,
        conson_config: ConsonModuleListConfig,
        telegram_service: TelegramService,
        accessory_driver: HomekitAccessoryDriver,
    ) -> None:
        """
        Initialize the HomeKit service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
            homekit_config: HomekitConfig for accessory configuration.
            conson_config: ConsonModuleListConfig for module configuration.
            telegram_service: TelegramService for parsing telegrams.
            accessory_driver: HomekitAccessoryDriver for pyhap integration.
        """
        self.logger = logging.getLogger(__name__)
        self._conbus_protocol = conbus_protocol
        self._homekit_config = homekit_config
        self._conson_config = conson_config
        self._telegram_service = telegram_service
        self._accessory_driver = accessory_driver
        self._connection_state = ConnectionState.DISCONNECTED
        self._state_machine = ConnectionState.create_state_machine()

        # Accessory states keyed by unique identifier (e.g., "A12_1")
        self._accessory_states: Dict[str, AccessoryState] = {}

        # Action key to accessory ID mapping
        self._action_map: Dict[str, str] = {}

        # Set up HomeKit callback
        self._accessory_driver.set_callback(self._on_homekit_set)

        # Track active level action: (accessory_id, action_type) or None
        self._active_level_action: Optional[tuple[str, str]] = None

        # Connect to protocol signals
        self._connect_signals()

        # Initialize accessory states from config
        self._initialize_accessory_states()

    def _initialize_accessory_states(self) -> None:
        """Initialize accessory states from HomekitConfig and ConsonModuleListConfig."""
        action_keys = "abcdefghijklmnopqrstuvwxyz0123456789"
        action_index = 0
        sort_order = 0

        for room in self._homekit_config.bridge.rooms:
            for accessory_name in room.accessories:
                accessory_config = self._find_accessory_config(accessory_name)
                if not accessory_config:
                    self.logger.warning(
                        f"Accessory config not found for {accessory_name}"
                    )
                    continue

                module_config = self._conson_config.find_module(
                    accessory_config.serial_number
                )
                if not module_config:
                    self.logger.warning(
                        f"Module config not found for {accessory_config.serial_number}"
                    )
                    continue

                # Create unique identifier
                accessory_id = (
                    f"{module_config.name}_{accessory_config.output_number + 1}"
                )

                # Assign action key
                action_key = (
                    action_keys[action_index] if action_index < len(action_keys) else ""
                )
                action_index += 1
                sort_order += 1

                state = AccessoryState(
                    room_name=room.name,
                    accessory_name=accessory_config.description
                    or accessory_config.name,
                    action=action_key,
                    output_state="?",
                    dimming_state="",
                    module_name=module_config.name,
                    serial_number=accessory_config.serial_number,
                    module_type=module_config.module_type,
                    error_status="OK",
                    output=accessory_config.output_number + 1,  # 1-based
                    sort=sort_order,
                    last_update=None,
                    toggle_action=accessory_config.toggle_action,
                )

                self._accessory_states[accessory_id] = state
                if action_key:
                    self._action_map[action_key] = accessory_id

    def _find_accessory_config(self, name: str) -> Optional[HomekitAccessoryConfig]:
        """
        Find accessory config by name.

        Args:
            name: Accessory name to find.

        Returns:
            HomekitAccessoryConfig if found, None otherwise.
        """
        for accessory in self._homekit_config.accessories:
            if accessory.name == name:
                return accessory
        return None

    def _find_accessory_config_by_output(
        self, serial_number: str, output: int
    ) -> Optional[HomekitAccessoryConfig]:
        """
        Find accessory config by serial number and output.

        Args:
            serial_number: Module serial number.
            output: Output number (1-based).

        Returns:
            HomekitAccessoryConfig if found, None otherwise.
        """
        for accessory in self._homekit_config.accessories:
            if (
                accessory.serial_number == serial_number
                and accessory.output_number == output - 1
            ):
                return accessory
        return None

    def _find_accessory_config_by_id(
        self, accessory_id: str
    ) -> Optional[HomekitAccessoryConfig]:
        """
        Find accessory config by accessory ID.

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            HomekitAccessoryConfig if found, None otherwise.
        """
        state = self._accessory_states.get(accessory_id)
        if not state:
            return None
        return self._find_accessory_config_by_output(state.serial_number, state.output)

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
        """
        Get current connection state.

        Returns:
            Current connection state.
        """
        return self._connection_state

    @property
    def server_info(self) -> str:
        """
        Get server connection info (IP:port).

        Returns:
            Server address in format "IP:port".
        """
        return f"{self._conbus_protocol.cli_config.ip}:{self._conbus_protocol.cli_config.port}"

    @property
    def accessory_states(self) -> List[AccessoryState]:
        """
        Get all accessory states.

        Returns:
            List of all accessory states.
        """
        accessories = list(self._accessory_states.values())
        # Sort modules by link_number
        accessories.sort(key=lambda a: a.sort)
        return accessories

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

    async def start(self) -> None:
        """Start the service and AccessoryDriver."""
        self.connect()
        await self._accessory_driver.start()

    async def stop(self) -> None:
        """Stop the AccessoryDriver and cleanup."""
        await self._accessory_driver.stop()
        self.cleanup()

    def _on_homekit_set(
        self, accessory_name: str, is_on: bool, brightness: Optional[int]
    ) -> None:
        """
        Handle HomeKit app set request (on/off or brightness).

        Args:
            accessory_name: Accessory name from HomeKit.
            is_on: True for on, False for off.
            brightness: Brightness value 0-100, or None for on/off only.
        """
        config = self._find_accessory_config(accessory_name)
        if not config:
            self.logger.warning(f"No config found for accessory: {accessory_name}")
            return

        if brightness is not None:
            # Handle brightness change
            self._handle_brightness_change(accessory_name, config, brightness)
        else:
            # Handle on/off toggle
            action = config.on_action if is_on else config.off_action
            self.send_action(action)
            self.on_status_message.emit(
                f"HomeKit: {accessory_name} {'ON' if is_on else 'OFF'}"
            )

    def _handle_brightness_change(
        self,
        accessory_name: str,
        config: "HomekitAccessoryConfig",
        target_brightness: int,
    ) -> None:
        """
        Handle brightness change by sending dimup/dimdown actions.

        Calculates delta from current brightness and sends appropriate
        number of LEVELINC or LEVELDEC commands (step = 10%).

        Args:
            accessory_name: Accessory name.
            config: Accessory configuration.
            target_brightness: Target brightness 0-100.
        """
        current = self._accessory_driver.get_brightness(accessory_name)
        delta = target_brightness - current

        if delta == 0:
            return

        # Determine action and steps (10% per step)
        step_size = 10
        steps = abs(delta) // step_size

        if delta > 0:
            # Increase brightness
            if not config.dimup_action:
                self.logger.warning(f"No dimup_action for {accessory_name}")
                return
            action = config.dimup_action
            direction = "+"
        else:
            # Decrease brightness
            if not config.dimdown_action:
                self.logger.warning(f"No dimdown_action for {accessory_name}")
                return
            action = config.dimdown_action
            direction = "-"

        # Send action for each step
        for _ in range(steps):
            self.send_action(action)

        self.on_status_message.emit(
            f"HomeKit: {accessory_name} {current}% → {target_brightness}% ({direction}{steps * step_size}%)"
        )

    def send_action(self, action: str) -> None:
        """
        Send an action telegram to the conbus protocol.

        Args:
            action: The action string to send (e.g., "E00L00I00").
        """
        self._conbus_protocol.send_raw_telegram(f"{action}M")
        self._conbus_protocol.send_raw_telegram(f"{action}B")

    def toggle_connection(self) -> None:
        """
        Toggle connection state between connected and disconnected.

        Disconnects if currently connected or connecting. Connects if currently
        disconnected or failed.
        """
        if self._connection_state in (
            ConnectionState.CONNECTED,
            ConnectionState.CONNECTING,
        ):
            self.disconnect()
        else:
            self.connect()

    def select_accessory(self, action_key: str) -> Optional[str]:
        """
        Get accessory ID for action key.

        Args:
            action_key: Action key (a-z0-9).

        Returns:
            Accessory ID if found, None otherwise.
        """
        return self._action_map.get(action_key)

    def toggle_selected(self, accessory_id: str) -> bool:
        """
        Toggle accessory by ID.

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if toggle was sent, False otherwise.
        """
        state = self._accessory_states.get(accessory_id)
        if not state or not state.toggle_action:
            self.logger.warning(f"No toggle_action for accessory {accessory_id}")
            return False

        self.send_action(state.toggle_action)
        self.on_status_message.emit(f"Toggling {state.accessory_name}")
        return True

    def turn_on_selected(self, accessory_id: str) -> bool:
        """
        Turn on accessory by ID.

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if on command was sent, False otherwise.
        """
        config = self._find_accessory_config_by_id(accessory_id)
        state = self._accessory_states.get(accessory_id)
        if not config or not state:
            self.logger.warning(f"No config for accessory {accessory_id}")
            return False

        self.send_action(config.on_action)
        self.on_status_message.emit(f"Turning ON {state.accessory_name}")
        return True

    def turn_off_selected(self, accessory_id: str) -> bool:
        """
        Turn off accessory by ID.

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if off command was sent, False otherwise.
        """
        config = self._find_accessory_config_by_id(accessory_id)
        state = self._accessory_states.get(accessory_id)
        if not config or not state:
            self.logger.warning(f"No config for accessory {accessory_id}")
            return False

        self.send_action(config.off_action)
        self.on_status_message.emit(f"Turning OFF {state.accessory_name}")
        return True

    def increase_dimmer(self, accessory_id: str) -> bool:
        """
        Increase dimmer level for accessory.

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if command was sent, False otherwise.
        """
        config = self._find_accessory_config_by_id(accessory_id)
        state = self._accessory_states.get(accessory_id)
        if not config or not state or not config.dimup_action:
            self.logger.warning(f"No config for accessory {accessory_id}")
            return False

        self.send_action(config.dimup_action)
        self.on_status_message.emit(f"Dim+ {state.accessory_name}")
        return True

    def decrease_dimmer(self, accessory_id: str) -> bool:
        """
        Decrease dimmer level for accessory.

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if command was sent, False otherwise.
        """
        config = self._find_accessory_config_by_id(accessory_id)
        state = self._accessory_states.get(accessory_id)
        if not config or not state or not config.dimdown_action:
            self.logger.warning(f"No config for accessory {accessory_id}")
            return False

        self.send_action(config.dimdown_action)
        self.on_status_message.emit(f"Dim- {state.accessory_name}")
        return True

    def levelup_selected(self, accessory_id: str) -> bool:
        """
        Increase level for accessory (toggle Make/Break).

        First press sends Make (M), second press sends Break (B).

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if command was sent, False otherwise.
        """
        config = self._find_accessory_config_by_id(accessory_id)
        state = self._accessory_states.get(accessory_id)
        if not config or not state or not config.levelup_action:
            self.logger.warning(f"No config for accessory {accessory_id}")
            return False

        return self._send_level_action(
            accessory_id, "levelup", config.levelup_action, state.accessory_name
        )

    def leveldown_selected(self, accessory_id: str) -> bool:
        """
        Decrease level for accessory (toggle Make/Break).

        First press sends Make (M), second press sends Break (B).

        Args:
            accessory_id: Accessory ID (e.g., "A12_1").

        Returns:
            True if command was sent, False otherwise.
        """
        config = self._find_accessory_config_by_id(accessory_id)
        state = self._accessory_states.get(accessory_id)
        if not config or not state or not config.leveldown_action:
            self.logger.warning(f"No config for accessory {accessory_id}")
            return False

        return self._send_level_action(
            accessory_id, "leveldown", config.leveldown_action, state.accessory_name
        )

    def _send_level_action(
        self, accessory_id: str, action_type: str, action: str, name: str
    ) -> bool:
        """
        Send level action with Make/Break toggle.

        Args:
            accessory_id: Accessory ID.
            action_type: "levelup" or "leveldown".
            action: Action code (e.g., "E02L13I15").
            name: Accessory name for status message.

        Returns:
            True if command was sent.
        """
        current = self._active_level_action

        # If same action is active, send Break and clear
        if current and current[0] == accessory_id and current[1] == action_type:
            self._conbus_protocol.send_raw_telegram(f"{action}B")
            self._active_level_action = None
            direction = "+" if action_type == "levelup" else "-"
            self.on_status_message.emit(f"Level{direction} {name} [B]")
            return True

        # If different action is active, send Break for it first
        if current:
            old_config = self._find_accessory_config_by_id(current[0])
            if old_config:
                old_action = (
                    old_config.levelup_action
                    if current[1] == "levelup"
                    else old_config.leveldown_action
                )
                if old_action:
                    self._conbus_protocol.send_raw_telegram(f"{old_action}B")

        # Send Make for new action
        self._conbus_protocol.send_raw_telegram(f"{action}M")
        self._active_level_action = (accessory_id, action_type)
        direction = "+" if action_type == "levelup" else "-"
        self.on_status_message.emit(f"Level{direction} {name} [M]")
        return True

    def refresh_all(self) -> None:
        """
        Refresh all module states.

        Queries module_output_state datapoint for eligible modules (XP24, XP33LR,
        XP33LED). Updates outputs column and last_update timestamp for each queried
        module.
        """
        self.on_status_message.emit("Refreshing module states...")

        # Eligible module types that support output state queries
        eligible_types = {"XP24", "XP33LR", "XP33LED"}

        # Track already queried serial numbers to avoid duplicates
        queried_serials: set[str] = set()

        for state in self._accessory_states.values():
            if (
                state.module_type in eligible_types
                and state.serial_number not in queried_serials
            ):
                self._query_module_output_state(state.serial_number)
                queried_serials.add(state.serial_number)
                self.logger.debug(
                    f"Querying output state for {state.module_name} ({state.module_type})"
                )

    def _query_module_output_state(self, serial_number: str) -> None:
        """
        Query module output state datapoint.

        Args:
            serial_number: Module serial number to query.
        """
        self._conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(DataPointType.MODULE_OUTPUT_STATE.value),
        )

    def _on_connection_made(self) -> None:
        """Handle connection made event."""
        if self._state_machine.transition("connected", ConnectionState.CONNECTED):
            self._connection_state = ConnectionState.CONNECTED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connected to {self.server_info}")

            # Emit initial accessory list
            self.on_room_list_updated.emit(self.accessory_states)

    def _on_connection_failed(self, failure: Exception) -> None:
        """
        Handle connection failed event.

        Args:
            failure: Exception that caused the failure.
        """
        if self._state_machine.transition("failed", ConnectionState.FAILED):
            self._connection_state = ConnectionState.FAILED
            self.on_connection_state_changed.emit(self._connection_state)
            self.on_status_message.emit(f"Connection failed: {failure}")

    def _on_telegram_received(self, event: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

        Routes telegrams to appropriate handlers based on type.

        Args:
            event: Telegram received event.
        """
        if event.telegram_type == TelegramType.REPLY:
            self._handle_reply_telegram(event)
        elif event.telegram_type == TelegramType.EVENT:
            self._handle_event_telegram(event)

    def _handle_reply_telegram(self, event: TelegramReceivedEvent) -> None:
        """
        Handle reply telegram for datapoint queries.

        Args:
            event: Telegram received event.
        """
        serial_number = event.serial_number
        if not serial_number:
            return

        # Parse the reply telegram
        reply_telegram = self._telegram_service.parse_reply_telegram(event.frame)
        if not reply_telegram:
            return

        # Check if this is a module output state response
        if (
            reply_telegram.system_function == SystemFunction.READ_DATAPOINT
            and reply_telegram.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        ):
            self._update_outputs_from_reply(serial_number, reply_telegram.data_value)

    def _update_outputs_from_reply(self, serial_number: str, data_value: str) -> None:
        """
        Update accessory outputs from module output state reply.

        Args:
            serial_number: Module serial number.
            data_value: Output state data value from reply.
        """
        # Parse output state bits using TelegramOutputService
        outputs = TelegramOutputService.format_output_state(data_value)
        output_list = outputs.split() if outputs else []

        # Update all accessories for this serial_number
        for state in self._accessory_states.values():
            if state.serial_number == serial_number:
                output_index = state.output - 1  # Convert to 0-based

                if output_index < len(output_list):
                    is_on = output_list[output_index] == "1"
                    state.output_state = "ON" if is_on else "OFF"

                    # Update dimming state for dimmable modules
                    if state.is_dimmable():
                        state.dimming_state = "-" if not is_on else ""

                    # Sync to HomeKit
                    config = self._find_accessory_config_by_output(
                        serial_number, state.output
                    )
                    if config:
                        self._accessory_driver.update_state(config.name, is_on)
                else:
                    state.output_state = "?"

                state.last_update = datetime.now()
                self.on_module_state_changed.emit(state)

    def _handle_event_telegram(self, event: TelegramReceivedEvent) -> None:
        """
        Handle event telegram for output state changes.

        Args:
            event: Telegram received event.
        """
        event_telegram = self._telegram_service.parse_event_telegram(event.frame)
        if not event_telegram:
            return

        # Determine output number based on module type
        output_number = None

        if event_telegram.module_type == ModuleTypeCode.XP24.value:
            if 80 <= event_telegram.input_number <= 83:
                output_number = event_telegram.input_number - 80
            else:
                return

        elif event_telegram.module_type in (
            ModuleTypeCode.XP33.value,
            ModuleTypeCode.XP33LR.value,
            ModuleTypeCode.XP33LED.value,
        ):
            if 80 <= event_telegram.input_number <= 82:
                output_number = event_telegram.input_number - 80
            else:
                return
        else:
            return

        # Find accessories matching link number and output
        output_1_based = output_number + 1
        for state in self._accessory_states.values():
            module_config = self._conson_config.find_module(state.serial_number)
            if not module_config:
                continue

            if (
                module_config.link_number == event_telegram.link_number
                and state.output == output_1_based
            ):
                # Update output state (M=ON, B=OFF)
                is_on = event_telegram.is_button_press
                state.output_state = "ON" if is_on else "OFF"

                # Update dimming state for dimmable modules
                if state.is_dimmable():
                    state.dimming_state = "-" if not is_on else ""

                # Sync to HomeKit
                config = self._find_accessory_config_by_output(
                    state.serial_number, state.output
                )
                if config:
                    self._accessory_driver.update_state(config.name, is_on)

                state.last_update = datetime.now()
                self.on_module_state_changed.emit(state)

                self.logger.debug(
                    f"Updated {state.accessory_name} to {'ON' if is_on else 'OFF'}"
                )

    def _on_timeout(self) -> None:
        """Handle timeout event."""
        self.on_status_message.emit("Waiting for action")

    def _on_failed(self, failure: Exception) -> None:
        """
        Handle protocol failure event.

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
        self.logger.debug("HomekitService cleaned up")

    def __enter__(self) -> "HomekitService":
        """
        Context manager entry.

        Returns:
            Self for context manager.
        """
        return self

    def __exit__(self, _exc_type: object, _exc_val: object, _exc_tb: object) -> None:
        """
        Context manager exit.

        Args:
            _exc_type: Exception type.
            _exc_val: Exception value.
            _exc_tb: Exception traceback.
        """
        self.cleanup()
