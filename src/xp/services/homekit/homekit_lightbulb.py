import logging

from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.telegram.action_type import ActionType
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.conbus_output_service import ConbusOutputService
from xp.services.telegram.telegram_output_service import TelegramOutputService


class LightBulb(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
        output_service: ConbusOutputService,
        telegram_output_service: TelegramOutputService,
        datapoint_service: ConbusDatapointService,
    ):
        super().__init__(driver, accessory.description)

        self.logger = logging.getLogger(__name__)
        self.accessory = accessory
        self.module = module

        self.output_service = output_service
        self.telegram_output_service = telegram_output_service
        self.datapoint_service = datapoint_service

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

    def available(self) -> bool:
        self.logger.debug("available")
        response = self.datapoint_service.query_datapoint(
            datapoint_type=DataPointType.MODULE_TYPE,
            serial_number=self.module.serial_number,
        )
        self.logger.debug(f"result: {response}")
        if response.datapoint_telegram is not None:
            return response.datapoint_telegram.data_value == "00"

        return False

    def set_on(self, value: bool) -> None:
        # Emit event using PyDispatcher
        self.logger.debug(f"set_on: {bool}")
        result = self.output_service.send_action(
            serial_number=self.module.serial_number,
            output_number=self.accessory.output_number,
            action_type=(ActionType.ON_RELEASE if value else ActionType.OFF_PRESS),
        )
        self.logger.debug(f"result: {result}")

    def get_on(self) -> bool:
        # Emit event and get response
        self.logger.debug("get_on")
        response = self.output_service.get_output_state(
            serial_number=self.module.serial_number,
        )
        if not response.success or not response.datapoint_telegram:
            self.logger.debug(f"result: {response}")
            return False

        data_value = response.datapoint_telegram.data_value
        raw_telegram = response.datapoint_telegram.raw_telegram

        self.logger.debug(
            f"result: {data_value}, output_number: {self.accessory.output_number}"
        )
        result = self.telegram_output_service.parse_status_response(raw_telegram)
        is_on = result[self.accessory.output_number]
        self.logger.debug(f" is_on: {is_on}")
        return is_on
