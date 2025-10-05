import asyncio
import logging

from bubus import EventBus
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_OUTLET

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import (
    OutletGetInUseEvent,
    OutletGetOnEvent,
    OutletSetInUseEvent,
    OutletSetOnEvent,
)


class Outlet(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_OUTLET
    event_bus: EventBus

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
        event_bus: EventBus,
    ):
        super().__init__(driver=driver, display_name=accessory.description)

        self.logger = logging.getLogger(__name__)
        self.accessory = accessory
        self.module = module

        self.event_bus = event_bus
        self.logger.info(
            "Creating Outlet { serial_number : %s, output_number: %s }",
            module.serial_number,
            accessory.output_number,
        )

        serial = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = ("XP24_outlet",)
        serv_outlet = self.add_preload_service("Outlet")
        self.set_info_service(version, manufacturer, model, serial)

        self.char_on = serv_outlet.configure_char(
            "On", setter_callback=self.set_on, getter_callback=self.get_on
        )
        self.char_outlet_in_use = serv_outlet.configure_char(
            "OutletInUse",
            setter_callback=self.set_outlet_in_use,
            getter_callback=self.get_outlet_in_use,
        )

    def set_outlet_in_use(self, value: bool) -> None:
        self.logger.debug(f"set_outlet_in_use: {bool}")
        self.event_bus.dispatch(
            OutletSetInUseEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                value=value
            )
        )

    def get_outlet_in_use(self) -> bool:
        # Emit event and get response
        self.logger.debug("get_outlet_in_use")
        return asyncio.run(self._async_get_outlet_in_use())

    async def _async_get_outlet_in_use(self) -> bool:
        """Async helper for get_outlet_in_use"""
        event = await self.event_bus.dispatch(
            OutletGetInUseEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        returned_value: bool = await event.event_result(timeout=1)
        return returned_value

    def set_on(self, value: bool) -> None:
        # Emit event using PyDispatcher
        self.logger.debug(f"set_on: {bool}")
        self.event_bus.dispatch(
            OutletSetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                value=value
            )
        )

    def get_on(self) -> bool:
        # Emit event and get response
        self.logger.debug("get_on")
        return asyncio.run(self._async_get_on())

    async def _async_get_on(self) -> bool:
        """Async helper for get_on"""
        event = await self.event_bus.dispatch(
            OutletGetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        returned_value: bool = await event.event_result(timeout=1)
        return returned_value
