import logging

from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from xp.models.homekit_config import HomekitAccessoryConfig
from xp.models.homekit_conson_config import ConsonModuleConfig
from xp.services.conbus_lightlevel_service import ConbusLightlevelService


class DimmingLight(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB
    lightlevel_service = ConbusLightlevelService()
    accessory: HomekitAccessoryConfig
    module: ConsonModuleConfig

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
    ):
        super().__init__(driver, accessory.description)

        self.logger = logging.getLogger(__name__)
        self.accessory = accessory
        self.module = module

        self.logger.info(
            "Creating DimmingLight { serial_number : %s, output_number: %s }",
            module.serial_number,
            accessory.output_number,
        )

        serial = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = "XP33LED_Lightdimmer"
        serv_light = self.add_preload_service(
            "Lightbulb",
            [
                # The names here refer to the Characteristic name defined
                # in characteristic.json
                "Brightness"
            ],
        )
        self.set_info_service(version, manufacturer, model, serial)

        self.char_on = serv_light.configure_char(
            "On", getter_callback=self.get_on, setter_callback=self.set_on
        )
        self.char_brightness = serv_light.configure_char(
            "Brightness",
            value=100,
            getter_callback=self.get_brightness,
            setter_callback=self.set_brightness,
        )

    def set_on(self, value: bool) -> None:
        # Emit event using PyDispatcher
        self.logger.debug(f"set_on: {bool}")
        if value:
            result = self.lightlevel_service.turn_on(
                serial_number=self.module.serial_number,
                output_number=self.accessory.output_number,
            )
        else:
            result = self.lightlevel_service.turn_off(
                serial_number=self.module.serial_number,
                output_number=self.accessory.output_number,
            )
        self.logger.debug(f"result: {result}")

    def get_on(self) -> bool:
        # Emit event and get response
        self.logger.debug("get_on")
        result = self.lightlevel_service.get_lightlevel(
            serial_number=self.module.serial_number,
            output_number=self.accessory.output_number,
        )
        self.logger.debug(f"result: {result}")
        if not result.success or not result.level:
            return False

        return result.level >= 0

    def set_brightness(self, value: int) -> None:
        self.logger.debug("set_brightness")
        result = self.lightlevel_service.set_lightlevel(
            serial_number=self.module.serial_number,
            output_number=self.accessory.output_number,
            level=value,
        )
        self.logger.debug(f"result: {result}")

    def get_brightness(self) -> int:
        self.logger.debug("get_brightness")
        result = self.lightlevel_service.get_lightlevel(
            serial_number=self.module.serial_number,
            output_number=self.accessory.output_number,
        )
        self.logger.debug(f"result: {result}")
        if not result.success or not result.level:
            return 0

        return result.level
