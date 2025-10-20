"""HomeKit HAP Service for Apple HomeKit integration.

This module provides the main HAP (HomeKit Accessory Protocol) service.
"""

import logging
import signal
import threading
from datetime import datetime
from typing import Dict, List, Optional

from bubus import EventBus
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from typing_extensions import Union

import xp
from xp.models.homekit.homekit_accessory import TemperatureSensor
from xp.models.homekit.homekit_config import (
    HomekitAccessoryConfig,
    HomekitConfig,
    RoomConfig,
)
from xp.models.protocol.conbus_protocol import (
    LightLevelReceivedEvent,
    ModuleStateChangedEvent,
    OutputStateReceivedEvent,
    ReadDatapointEvent,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.homekit.homekit_dimminglight import DimmingLight
from xp.services.homekit.homekit_lightbulb import LightBulb
from xp.services.homekit.homekit_module_service import HomekitModuleService
from xp.services.homekit.homekit_outlet import Outlet


class HomekitHapService:
    """HomeKit HAP service.

    Manages HAP accessory protocol, handles bridge and accessory setup,
    and processes HomeKit events for device state synchronization.

    Attributes:
        event_bus: Event bus for inter-service communication.
        last_activity: Timestamp of last service activity.
        logger: Logger instance.
        config: HomeKit configuration.
        accessory_registry: Registry of accessories by identifier.
        module_registry: Registry of accessories by module key.
        modules: Module service for module lookup.
        driver: HAP accessory driver.
    """

    event_bus: EventBus

    def __init__(
        self,
        homekit_config: HomekitConfig,
        module_service: HomekitModuleService,
        event_bus: EventBus,
    ):
        """Initialize the HomeKit HAP service.

        Args:
            homekit_config: HomeKit configuration.
            module_service: Module service for dependency injection.
            event_bus: Event bus for dependency injection.
        """
        self.last_activity: Optional[datetime] = None

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = homekit_config
        self.accessory_registry: Dict[str, Union[LightBulb, Outlet, DimmingLight]] = {}
        self.module_registry: Dict[
            tuple[int, int], List[Union[LightBulb, Outlet, DimmingLight]]
        ] = {}

        # Service dependencies
        self.modules = module_service
        self.event_bus = event_bus

        # Subscribe to events
        self.event_bus.on(ModuleStateChangedEvent, self.handle_module_state_changed)
        self.event_bus.on(OutputStateReceivedEvent, self.handle_output_state_received)
        self.event_bus.on(LightLevelReceivedEvent, self.handle_light_level_received)

        # We want SIGTERM (terminate) to be handled by the driver itself,
        # so that it can gracefully stop the accessory, server and advertising.
        driver = AccessoryDriver(
            port=self.config.homekit.port,
        )
        signal.signal(signal.SIGTERM, driver.signal_handler)
        self.driver: AccessoryDriver = driver

    async def async_start(self) -> None:
        """Start the HAP service asynchronously."""
        self.logger.info("Loading accessories.")
        self.build_bridge()
        self.logger.info("Accessories loaded successfully")

        # Start HAP-python in a separate thread to avoid event loop conflicts
        self.logger.info("Starting HAP-python driver in separate thread.")
        hap_thread = threading.Thread(
            target=self._run_driver_in_thread, daemon=True, name="HAP-Python"
        )
        hap_thread.start()
        self.logger.info("HAP-python driver thread started")

    def _run_driver_in_thread(self) -> None:
        """Run the HAP-python driver in a separate thread with its own event loop."""
        try:
            self.logger.info("HAP-python thread starting, creating new event loop.")
            # Create a new event loop for this thread

            self.logger.info("Starting HAP-python driver.")
            self.driver.start()
            self.logger.info("HAP-python driver started successfully")
        except Exception as e:
            self.logger.error(f"HAP-python driver error: {e}", exc_info=True)

    def handle_output_state_received(self, event: OutputStateReceivedEvent) -> str:
        """Handle output state received event.

        Args:
            event: Output state received event.

        Returns:
            Data value from the event.
        """
        self.logger.debug(f"Received OutputStateReceivedEvent {event}")
        output_number = 0
        for output in event.data_value[::-1]:
            if output == "x":
                break
            identifier = f"{event.serial_number}.{output_number:02X}"
            accessory = self.accessory_registry.get(identifier)

            if not accessory:
                self.logger.warning(f"Invalid accessory: {identifier} (not found)")
            else:
                accessory.is_on = True if output == "1" else False
            output_number += 1

        self.logger.debug(
            f"handle_output_state_received "
            f"serial_number: {event.serial_number}, "
            f"data_vale: {event.data_value}"
        )
        return event.data_value

    def handle_light_level_received(self, event: LightLevelReceivedEvent) -> str:
        """Handle light level received event.

        Args:
            event: Light level received event.

        Returns:
            Data value from the event.
        """
        # Parse response format like "00:050,01:025,02:100"
        self.logger.debug("Received LightLevelReceivedEvent", extra={"event": event})
        output_number = 0
        for output_data in event.data_value.split(","):
            if ":" in output_data:
                output_str, level_str = output_data.split(":")
                level_str = level_str.replace("[%]", "")
                output_number = int(output_str)
                brightness = int(level_str)
                identifier = f"{event.serial_number}.{output_number:02X}"
                accessory = self.accessory_registry.get(identifier)

                if not accessory:
                    self.logger.warning(
                        f"Invalid accessory: {event.serial_number} (not found)"
                    )
                elif not isinstance(accessory, DimmingLight):
                    self.logger.warning(
                        f"Invalid accessory: {event.serial_number} (not dimming light)"
                    )
                else:
                    accessory.brightness = brightness

            output_number += 1

        self.logger.debug(
            f"handle_light_level_received "
            f"serial_number: {event.serial_number}, "
            f"data_vale: {event.data_value}"
        )
        return event.data_value

    def build_bridge(self) -> None:
        """Build the HomeKit bridge with all configured accessories."""
        bridge_config = self.config.bridge
        bridge = Bridge(self.driver, bridge_config.name)
        bridge.set_info_service(
            xp.__version__, xp.__manufacturer__, xp.__model__, xp.__serial__
        )

        for room in bridge_config.rooms:
            self.add_room(bridge, room)

        self.driver.add_accessory(accessory=bridge)

    def add_room(self, bridge: Bridge, room: RoomConfig) -> None:
        """Add a room with its accessories to the bridge.

        Args:
            bridge: HAP bridge instance.
            room: Room configuration.
        """
        temperature = TemperatureSensor(self.driver, room.name)
        bridge.add_accessory(temperature)

        for accessory_name in room.accessories:
            homekit_accessory = self.get_accessory_by_name(accessory_name)
            if homekit_accessory is None:
                self.logger.warning("Accessory '{}' not found".format(accessory_name))
                continue

            accessory = self.get_accessory(homekit_accessory)
            if accessory:
                bridge.add_accessory(accessory)
                # Add to accessory_registry
                self.accessory_registry[accessory.identifier] = accessory

                # Add to module_registry for event-driven lookup
                module_key = (
                    accessory.module.module_type_code,
                    accessory.module.link_number,
                )
                if module_key not in self.module_registry:
                    self.module_registry[module_key] = []
                self.module_registry[module_key].append(accessory)

    def get_accessory(
        self, homekit_accessory: HomekitAccessoryConfig
    ) -> Union[LightBulb, Outlet, DimmingLight, None]:
        """Get an accessory instance from configuration.

        Args:
            homekit_accessory: HomeKit accessory configuration.

        Returns:
            Accessory instance or None if not found or invalid service type.
        """
        module_config = self.modules.get_module_by_serial(
            homekit_accessory.serial_number
        )
        if module_config is None:
            self.logger.warning(f"Accessory '{homekit_accessory.name}' not found")
            return None

        if homekit_accessory.service == "lightbulb":
            return LightBulb(
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
                event_bus=self.event_bus,
            )

        if homekit_accessory.service == "outlet":
            return Outlet(
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
                event_bus=self.event_bus,
            )

        if homekit_accessory.service == "dimminglight":
            return DimmingLight(
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
                event_bus=self.event_bus,
            )

        self.logger.warning(f"Accessory '{homekit_accessory.name}' not found")
        return None

    def get_accessory_by_name(self, name: str) -> Optional[HomekitAccessoryConfig]:
        """Get an accessory configuration by name.

        Args:
            name: Name of the accessory to find.

        Returns:
            Accessory configuration if found, None otherwise.
        """
        return next(
            (module for module in self.config.accessories if module.name == name), None
        )

    def handle_module_state_changed(self, event: ModuleStateChangedEvent) -> None:
        """Handle module state change by refreshing affected accessories.

        Args:
            event: Module state changed event.
        """
        self.logger.debug(
            f"Module state changed: module_type={event.module_type_code}, "
            f"link={event.link_number}, input={event.input_number}"
        )

        # O(1) lookup using module_registry
        module_key = (event.module_type_code, event.link_number)
        affected_accessories = self.module_registry.get(module_key, [])

        if not affected_accessories:
            self.logger.debug(
                f"No accessories found for module_type={event.module_type_code}, "
                f"link={event.link_number}"
            )
            return

        # Request cache refresh for each affected accessory
        for accessory in affected_accessories:
            self.logger.info(
                f"Requesting cache refresh for accessory: {accessory.identifier}"
            )

            # Request OUTPUT_STATE refresh
            self.event_bus.dispatch(
                ReadDatapointEvent(
                    serial_number=accessory.module.serial_number,
                    datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
                    refresh_cache=True,
                )
            )

            # If dimming light, also refresh LIGHT_LEVEL
            if isinstance(accessory, DimmingLight):
                self.event_bus.dispatch(
                    ReadDatapointEvent(
                        serial_number=accessory.module.serial_number,
                        datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
                        refresh_cache=True,
                    )
                )
