"""HomeKit Dimming Light Accessory.

This module provides a dimming light accessory for HomeKit integration.
"""

import logging

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
    DimmingLightSetOnEvent,
)


class DimmingLight(Accessory):
    """HomeKit dimming light accessory.

    Attributes:
        category: HomeKit category (CATEGORY_LIGHTBULB).
        event_bus: Event bus for inter-service communication.
        logger: Logger instance.
        identifier: Unique identifier for the accessory.
        accessory: Accessory configuration.
        module: Module configuration.
        is_on: Current on/off state.
        brightness: Current brightness level (0-100).
        char_on: On characteristic.
        char_brightness: Brightness characteristic.
    """

    category = CATEGORY_LIGHTBULB
    event_bus: EventBus

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
        event_bus: EventBus,
    ):
        """Initialize the dimming light accessory.

        Args:
            driver: HAP accessory driver.
            module: Module configuration.
            accessory: Accessory configuration.
            event_bus: Event bus for inter-service communication.
        """
        super().__init__(driver, accessory.description)

        self.logger = logging.getLogger(__name__)

        identifier = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = "XP33LED_Lightdimmer"

        self.identifier = identifier
        self.accessory = accessory
        self.module = module
        self.event_bus = event_bus

        self.is_on: bool = True
        self.brightness: int = 0

        self.logger.info(
            "Creating DimmingLight { serial_number : %s, output_number: %s }",
            module.serial_number,
            accessory.output_number,
        )

        serv_light = self.add_preload_service(
            "Lightbulb",
            [
                # The names here refer to the Characteristic name defined
                # in characteristic.json
                "Brightness"
            ],
        )
        self.set_info_service(version, manufacturer, model, identifier)

        self.char_on = serv_light.configure_char(
            "On", getter_callback=self.get_on, setter_callback=self.set_on, value=False
        )
        self.char_brightness = serv_light.configure_char(
            "Brightness",
            value=100,
            getter_callback=self.get_brightness,
            setter_callback=self.set_brightness,
        )
        self.logger.debug(f"char_on properties: {self.char_on.properties}")
        self.logger.debug(
            f"char_brightness properties: {self.char_brightness.properties}"
        )

    def set_on(self, value: bool) -> None:
        """Set the on/off state of the dimming light.

        Args:
            value: True to turn on, False to turn off.
        """
        # Emit set event
        self.logger.debug(f"set_on {value}")

        if value != self.is_on:
            self.is_on = value
            self.event_bus.dispatch(
                DimmingLightSetOnEvent(
                    serial_number=self.accessory.serial_number,
                    output_number=self.accessory.output_number,
                    module=self.module,
                    accessory=self.accessory,
                    value=value,
                    brightness=self.brightness,
                )
            )

    def get_on(self) -> bool:
        """Get the on/off state of the dimming light.

        Returns:
            True if on, False if off.
        """
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
        """Set the brightness level of the dimming light.

        Args:
            value: Brightness level (0-100).
        """
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
        """Get the brightness level of the dimming light.

        Returns:
            Current brightness level (0-100).
        """
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
