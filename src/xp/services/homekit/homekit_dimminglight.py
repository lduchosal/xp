import logging
from typing import Optional

from bubus import EventBus
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from xp.models.homekit.homekit_config import HomekitAccessoryConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import (
    DimmingLightGetBrightnessEvent,
    DimmingLightGetOnEvent,
    DimmingLightSetBrightnessEvent,
    DimmingLightSetOnEvent, DatapointReceivedEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


class DimmingLight(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB
    event_bus: EventBus

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
        event_bus: EventBus
    ):
        super().__init__(driver, accessory.description)

        self.logger = logging.getLogger(__name__)
        self.accessory = accessory
        self.module = module
        self.event_bus = event_bus

        self.is_on: bool = True
        self.brightness: int = 0

        self.event_bus.on(DatapointReceivedEvent, self.on_is_on_received)
        self.event_bus.on(DatapointReceivedEvent, self.on_brightness_received)

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
            "On",
            getter_callback=self.get_on,
            setter_callback=self.set_on,
            value=False
        )
        self.char_brightness = serv_light.configure_char(
            "Brightness",
            value=100,
            getter_callback=self.get_brightness,
            setter_callback=self.set_brightness,
        )

    def on_is_on_received(self, event: DatapointReceivedEvent) -> Optional[bool]:

        if (event.serial_number != self.module.serial_number
            or event.datapoint_type != DataPointType.MODULE_OUTPUT_STATE
        ):
            return None

        is_on = event.data_value[::-1][self.accessory.output_number] == "1"
        self.logger.debug(
            f"on_is_on_received "
            f"serial_number: {event.serial_number}, "
            f"output_number: {self.accessory.output_number}, "
            f"data_vale: {event.data_value}"
            f"is_on: {is_on}"
        )
        self.is_on = is_on
        return is_on

    def on_brightness_received(self, event: DatapointReceivedEvent) -> Optional[int]:

        if (event.serial_number != self.module.serial_number
            or event.datapoint_type != DataPointType.MODULE_LIGHT_LEVEL
        ):
            return None

        # Parse response format like "00:050,01:025,02:100"
        data_value = event.data_value
        self.logger.debug(f"Parsing brightness from response: {data_value}")
        brightness = 0
        for output_data in data_value.split(","):
            if ":" in output_data:
                output_str, level_str = output_data.split(":")
                if int(output_str) == self.accessory.output_number:
                    brightness = int(level_str)
                    break

        self.logger.debug(
            f"on_brightness_received "
            f"serial_number: {event.serial_number}, "
            f"output_number: {self.accessory.output_number}, "
            f"data_vale: {event.data_value}"
            f"brightness: {brightness}"
        )
        self.brightness = brightness
        return brightness

    def set_on(self, value: bool) -> None:
        # Emit set event
        self.logger.debug(f"set_on {value}")

        self.is_on = value
        self.event_bus.dispatch(
            DimmingLightSetOnEvent(
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

        # Dispatch event from HAP thread (thread-safe)
        self.event_bus.dispatch(
            DimmingLightGetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        return self.is_on


    def set_brightness(self, value: int) -> None:
        self.logger.debug(f"set_brightness {value}")
        self.brightness = value

        self.event_bus.dispatch(
            DimmingLightSetBrightnessEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                brightness=value,
            )
        )

    def get_brightness(self) -> int:
        self.logger.debug("get_brightness")

        # Dispatch event from HAP thread (thread-safe)
        self.event_bus.dispatch(
            DimmingLightGetBrightnessEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        return self.brightness
