import logging
import signal
from datetime import datetime
from typing import Optional

from pyhap.accessory import Bridge, Accessory
from pyhap.accessory_driver import AccessoryDriver
from typing_extensions import Union

import xp
from xp.models.homekit_accessory import TemperatureSensor
from xp.services.homekit_outlet import Outlet
from xp.services.homekit_lightbulb import LightBulb
from xp.models.homekit_config import HomekitConfig, HomekitAccessoryConfig, RoomConfig
from xp.services.homekit_dimminglight import DimmingLight
from xp.services.homekit_module_service import HomekitModuleService


class HomekitService:
    """
    HomeKit services.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        homekit_config_path: str = "homekit.yml",
        conson_config_path: str = "conson.yml",
    ):
        """Initialize the Conbus client send service"""
        self.last_activity: Optional[datetime] = None

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = HomekitConfig.from_yaml(homekit_config_path)
        self.modules = HomekitModuleService(conson_config_path)

        # We want SIGTERM (terminate) to be handled by the driver itself,
        # so that it can gracefully stop the accessory, server and advertising.
        driver = AccessoryDriver(
            port=self.config.homekit.port,
        )
        signal.signal(signal.SIGTERM, driver.signal_handler)
        self.driver: AccessoryDriver = driver

    def run(self) -> None:
        """Get current client configuration"""
        self.load_accessories()

        # Start it!
        self.driver.start()

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
            self.logger.warning(
                "Accessory '{}' not found".format(homekit_accessory.name)
            )
            return None

        if homekit_accessory.service == "lightbulb":
            return LightBulb(
                driver=self.driver, module=module_config, accessory=homekit_accessory
            )

        if homekit_accessory.service == "outlet":
            return Outlet(
                driver=self.driver, module=module_config, accessory=homekit_accessory
            )

        if homekit_accessory.service == "dimminglight":
            return DimmingLight(
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
            )

        self.logger.warning("Accessory '{}' not found".format(homekit_accessory.name))
        return None

    def get_accessory_by_name(self, name: str) -> Optional[HomekitAccessoryConfig]:
        return next(
            (module for module in self.config.accessories if module.name == name), None
        )
