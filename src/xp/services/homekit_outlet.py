import logging

from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_OUTLET

from xp.models.action_type import ActionType
from xp.models.homekit_config import HomekitAccessoryConfig
from xp.models.homekit_conson_config import ConsonModuleConfig
from xp.services.conbus_output_service import ConbusOutputService
from xp.services.telegram_output_service import TelegramOutputService


class Outlet(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_OUTLET
    output_service = ConbusOutputService()
    telegram_output_service = TelegramOutputService()

    accessory: HomekitAccessoryConfig
    module: ConsonModuleConfig

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
    ):
        super().__init__(driver=driver, display_name=accessory.description)

        self.logger = logging.getLogger(__name__)
        self.accessory = accessory
        self.module = module

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
        result = self.output_service.send_action(
            serial_number=self.module.serial_number,
            output_number=self.accessory.output_number,
            action_type=(ActionType.ON_RELEASE if value else ActionType.OFF_PRESS),
        )
        self.logger.debug(f"result: {result}")

    def get_outlet_in_use(self) -> bool:
        # Emit event and get response
        self.logger.debug("get_on")
        response = self.output_service.get_output_state(
            serial_number=self.module.serial_number,
        )
        self.logger.debug(f"result: {response}")
        if response.received_telegrams:
            result = self.telegram_output_service.parse_status_response(
                response.received_telegrams[0]
            )
            return result[3 - self.accessory.output_number]

        return False

    def set_on(self, value: bool) -> None:
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
        self.logger.debug(f"result: {response}")
        if response.received_telegrams:
            result = self.telegram_output_service.parse_status_response(
                response.received_telegrams[0]
            )
            return result[3 - self.accessory.output_number]

        return False
