import logging
import signal
from datetime import datetime
from typing import Optional

from pyhap.accessory import Bridge, Accessory
from pyhap.accessory_driver import AccessoryDriver
from typing_extensions import Union

from xp.models.homekit_accessory import LightBulb, Outlet
from xp.models.homekit_config import HomekitConfig, Room, HomekitAccessoryConfig
from xp.services.homekit_module_service import HomekitModuleService


class HomekitService:
    """
    HomeKit services.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """
    def __init__(self, homekit_config_path: str = "homekit.yml", conson_config_path: str = "conson.yml"):
        """Initialize the Conbus client send service"""
        self.last_activity: Optional[datetime] = None

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = HomekitConfig.from_yaml(homekit_config_path)
        self.modules = HomekitModuleService(conson_config_path)

        # We want SIGTERM (terminate) to be handled by the driver itself,
        # so that it can gracefully stop the accessory, server and advertising.
        driver = AccessoryDriver(port=self.config.homekit.port)
        signal.signal(signal.SIGTERM, driver.signal_handler)
        self.driver = driver

    def run(self) :

        """Get current client configuration"""
        self.load_accessories()

        # Start it!
        self.driver.start()

    def load_accessories(self):
        bridge = Bridge(self.driver, self.config.homekit.name)
        for room in self.config.rooms:
            self.add_room(bridge, room)

        self.driver.add_accessory(accessory=bridge)

    def add_room(self, bridge: Bridge, room: Room):
        """Call this method to get a Bridge instead of a standalone accessory."""
        for accessory_name in room.accessories:
            homekit_accessory = self.get_accessory_by_name(accessory_name)
            if homekit_accessory is None:
                self.logger.warning("Accessory '{}' not found".format(accessory_name))
                continue

            accessory = self.get_accessory(homekit_accessory)
            bridge.add_accessory(accessory)

        return bridge

    def get_accessory(self, homekit_accessory: HomekitAccessoryConfig) \
            -> Union[Accessory, LightBulb, Outlet, None]:
        """Call this method to get a standalone Accessory."""
        if homekit_accessory.service == "lightbulb":
            return LightBulb(self.driver, homekit_accessory.name)
        if homekit_accessory.service == "outlet":
            return Outlet(self.driver, homekit_accessory.name)
        self.logger.warning("Accessory '{}' not found".format(homekit_accessory.service))
        return None

    def get_accessory_by_name(self, name) -> Optional[HomekitAccessoryConfig]:
        return next((module for module in self.config.accessories if module.name == name), None)


