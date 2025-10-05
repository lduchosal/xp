import asyncio
import logging

from bubus import EventBus
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import LightBulbGetOnEvent, LightBulbSetOnEvent


class LightBulb(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB
    event_bus: EventBus

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
        event_bus: EventBus,
    ):
        super().__init__(driver, accessory.description)

        self.logger = logging.getLogger(__name__)
        self.accessory = accessory
        self.module = module
        self.event_bus = event_bus

        self.logger.info(
            "Creating Lightbulb { serial_number : %s, output_number: %s }",
            module.serial_number,
            accessory.output_number,
        )

        serial = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = ("XP24_lightbulb",)
        serv_light = self.add_preload_service("Lightbulb")
        self.set_info_service(version, manufacturer, model, serial)

        self.char_on = serv_light.configure_char(
            "On", getter_callback=self.get_on, setter_callback=self.set_on
        )

    def set_on(self, value: bool) -> None:
        # Emit event using PyDispatcher
        self.logger.debug(f"set_on: {bool}")
        self.event_bus.dispatch(
            LightBulbSetOnEvent(
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

        # Run the async event bus dispatch in the current event loop
        return asyncio.run(self._async_get_on())

    async def _async_get_on(self) -> bool:
        """Async helper for get_on"""
        self.logger.debug(f"_async_get_on")
        event = await self.event_bus.dispatch(
            LightBulbGetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        self.logger.debug(f"_async_get_on: dispatch")
        returned_value: bool = await event.event_result(timeout=1)
        self.logger.debug(f"_async_get_on: returned_value {returned_value}")
        return returned_value
