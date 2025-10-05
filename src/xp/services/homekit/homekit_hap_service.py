import logging
import signal
import threading
from datetime import datetime
from typing import Optional

from bubus import EventBus
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from typing_extensions import Union

import xp
from xp.models.homekit.homekit_accessory import TemperatureSensor
from xp.models.homekit.homekit_config import (
    HomekitAccessoryConfig,
    HomekitConfig,
    RoomConfig,
)
from xp.services.homekit.homekit_dimminglight import DimmingLight
from xp.services.homekit.homekit_lightbulb import LightBulb
from xp.services.homekit.homekit_module_service import HomekitModuleService
from xp.services.homekit.homekit_outlet import Outlet


class HomekitHapService:
    """
    HomeKit services.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    event_bus: EventBus

    def __init__(
        self,
        homekit_config: HomekitConfig,
        module_service: HomekitModuleService,
        event_bus: EventBus,
    ):
        """Initialize the Conbus client send service

        Args:
            homekit_config: Conson configuration file
            module_service: HomekitModuleService for dependency injection
            event_bus: EventBus for dependency injection
        """
        self.last_activity: Optional[datetime] = None

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = homekit_config

        # Service dependencies
        self.modules = module_service
        self.event_bus = event_bus

        # We want SIGTERM (terminate) to be handled by the driver itself,
        # so that it can gracefully stop the accessory, server and advertising.
        driver = AccessoryDriver(
            port=self.config.homekit.port,
        )
        signal.signal(signal.SIGTERM, driver.signal_handler)
        self.driver: AccessoryDriver = driver

    async def async_start(self) -> None:
        """Get current client configuration"""
        self.logger.info("Loading accessories...")
        self.load_accessories()
        self.logger.info("Accessories loaded successfully")

        # Start HAP-python in a separate thread to avoid event loop conflicts
        self.logger.info("Starting HAP-python driver in separate thread...")
        hap_thread = threading.Thread(target=self._run_driver_in_thread, daemon=True, name="HAP-Python")
        hap_thread.start()
        self.logger.info("HAP-python driver thread started")

    def _run_driver_in_thread(self) -> None:
        """Run the HAP-python driver in a separate thread with its own event loop"""
        try:
            self.logger.info("HAP-python thread starting, creating new event loop...")
            # Create a new event loop for this thread

            self.logger.info("Starting HAP-python driver...")
            self.driver.start()
            self.logger.info("HAP-python driver started successfully")
        except Exception as e:
            self.logger.error(f"HAP-python driver error: {e}", exc_info=True)

    def load_accessories(self) -> None:
        bridge_config = self.config.bridge
        bridge = Bridge(self.driver, bridge_config.name)
        bridge.set_info_service(
            xp.__version__, xp.__manufacturer__, xp.__model__, xp.__serial__
        )

        for room in bridge_config.rooms:
            self.add_room(bridge, room)

        self.driver.add_accessory(accessory=bridge)

    def add_room(self, bridge: Bridge, room: RoomConfig) -> None:
        """Call this method to get a Bridge instead of a standalone accessory."""
        temperature = TemperatureSensor(self.driver, room.name)
        bridge.add_accessory(temperature)

        for accessory_name in room.accessories:
            homekit_accessory = self.get_accessory_by_name(accessory_name)
            if homekit_accessory is None:
                self.logger.warning("Accessory '{}' not found".format(accessory_name))
                continue

            accessory = self.get_accessory(homekit_accessory)
            bridge.add_accessory(accessory)

    def get_accessory(
        self, homekit_accessory: HomekitAccessoryConfig
    ) -> Union[Accessory, LightBulb, Outlet, None]:
        """Call this method to get a standalone Accessory."""
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
        return next(
            (module for module in self.config.accessories if module.name == name), None
        )
