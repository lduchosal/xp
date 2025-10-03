import logging
import signal
from datetime import datetime
from typing import TYPE_CHECKING, Optional

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

from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.conbus_lightlevel_service import ConbusLightlevelService
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.homekit.homekit_cache_service import HomeKitCacheService
from xp.services.telegram.telegram_output_service import TelegramOutputService


class HomekitService:
    """
    HomeKit services.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        homekit_config: HomekitConfig,
        module_service: HomekitModuleService,
        output_service: ConbusOutputService,
        telegram_output_service: TelegramOutputService,
        datapoint_service: ConbusDatapointService,
        cache_service: HomeKitCacheService,
        lightlevel_service: ConbusLightlevelService,
    ):
        """Initialize the Conbus client send service

        Args:
            homekit_config: Conson configuration file
            module_service: HomekitModuleService for dependency injection
            output_service: ConbusOutputService for dependency injection
            telegram_output_service: TelegramOutputService for dependency injection
            datapoint_service: ConbusDatapointService for dependency injection
            cache_service: HomeKitCacheService for dependency injection
            lightlevel_service: ConbusLightlevelService for dependency injection
        """
        self.last_activity: Optional[datetime] = None

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = homekit_config

        # Service dependencies
        self.modules = module_service
        self.output_service = output_service
        self.telegram_output_service = telegram_output_service
        self.datapoint_service = datapoint_service
        self.cache_service = cache_service
        self.lightlevel_service = lightlevel_service

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
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
                output_service=self.output_service,
                telegram_output_service=self.telegram_output_service,
                datapoint_service=self.datapoint_service,
            )

        if homekit_accessory.service == "outlet":
            return Outlet(
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
                cache_service=self.cache_service,
                output_service=self.output_service,
                telegram_output_service=self.telegram_output_service,
            )

        if homekit_accessory.service == "dimminglight":
            return DimmingLight(
                driver=self.driver,
                module=module_config,
                accessory=homekit_accessory,
                lightlevel_service=self.lightlevel_service,
            )

        self.logger.warning("Accessory '{}' not found".format(homekit_accessory.name))
        return None

    def get_accessory_by_name(self, name: str) -> Optional[HomekitAccessoryConfig]:
        return next(
            (module for module in self.config.accessories if module.name == name), None
        )
