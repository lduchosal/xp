import logging
from typing import Optional

from bubus import EventBus
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import (
    DatapointReceivedEvent,
    LightBulbGetOnEvent,
    LightBulbSetOnEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


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
        self.is_on = False

        self.logger.info(
            "Creating Lightbulb { serial_number : %s, output_number: %s }",
            module.serial_number,
            accessory.output_number,
        )

        self.event_bus.on(DatapointReceivedEvent, self.on_datapoint_received)

        serial = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = ("XP24_lightbulb",)
        serv_light = self.add_preload_service("Lightbulb")
        self.set_info_service(version, manufacturer, model, serial)

        self.char_on = serv_light.configure_char(
            "On", getter_callback=self.get_on, setter_callback=self.set_on
        )

    def on_datapoint_received(self, event: DatapointReceivedEvent) -> Optional[bool]:

        if (
            event.serial_number != self.module.serial_number
            or event.datapoint_type != DataPointType.MODULE_OUTPUT_STATE
        ):
            return None

        is_on = event.data_value[::-1][self.accessory.output_number] == "1"
        self.is_on = is_on
        self.logger.debug(
            f"on_datapoint_received "
            f"serial_number: {event.serial_number}, "
            f"output_number: {self.accessory.output_number}, "
            f"data_vale: {event.data_value}"
            f"is_on: {is_on}"
        )
        return is_on

    def set_on(self, value: bool) -> None:
        # Emit set event
        self.logger.debug(f"set_on {value}")
        self.is_on = value
        self.event_bus.dispatch(
            LightBulbSetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                value=value,
            )
        )

    def get_on(self) -> bool:
        # Emit event and get response
        self.logger.debug("get_on")
        self.event_bus.dispatch(
            LightBulbGetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        self.logger.debug(f"get_on from dispatch: {self.is_on}")

        return self.is_on
