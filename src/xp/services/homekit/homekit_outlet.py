"""HomeKit Outlet Accessory.

This module provides an outlet accessory for HomeKit integration.
"""

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
    """HomeKit outlet accessory.

    Attributes:
        category: HomeKit category (CATEGORY_OUTLET).
        event_bus: Event bus for inter-service communication.
        logger: Logger instance.
        identifier: Unique identifier for the accessory.
        accessory: Accessory configuration.
        module: Module configuration.
        is_on: Current on/off state.
        is_in_use: Current in-use state.
        char_on: On characteristic.
        char_outlet_in_use: Outlet in-use characteristic.
    """

    category = CATEGORY_OUTLET
    event_bus: EventBus

    def __init__(
        self,
        driver: AccessoryDriver,
        module: ConsonModuleConfig,
        accessory: HomekitAccessoryConfig,
        event_bus: EventBus,
    ):
        """Initialize the outlet accessory.

        Args:
            driver: HAP accessory driver.
            module: Module configuration.
            accessory: Accessory configuration.
            event_bus: Event bus for inter-service communication.
        """
        super().__init__(driver=driver, display_name=accessory.description)

        self.logger = logging.getLogger(__name__)

        identifier = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = ("XP24_outlet",)

        self.identifier = identifier
        self.accessory = accessory
        self.module = module

        self.event_bus = event_bus
        self.logger.info(
            "Creating Outlet { serial_number : %s, output_number: %s }",
            module.serial_number,
            accessory.output_number,
        )
        self.is_on = False
        self.is_in_use = False

        serv_outlet = self.add_preload_service("Outlet")
        self.set_info_service(version, manufacturer, model, identifier)
        self.char_on = serv_outlet.configure_char(
            "On", setter_callback=self.set_on, getter_callback=self.get_on
        )
        self.char_outlet_in_use = serv_outlet.configure_char(
            "OutletInUse",
            setter_callback=self.set_outlet_in_use,
            getter_callback=self.get_outlet_in_use,
        )

    def set_outlet_in_use(self, value: bool) -> None:
        """Set the in-use state of the outlet.

        Args:
            value: True if in use, False otherwise.
        """
        self.logger.debug(f"set_outlet_in_use {value}")

        self.is_in_use = value
        self.event_bus.dispatch(
            OutletSetInUseEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                value=value,
            )
        )
        self.logger.debug(f"set_outlet_in_use {value} end")

    def get_outlet_in_use(self) -> bool:
        """Get the in-use state of the outlet.

        Returns:
            True if in use, False otherwise.
        """
        # Emit event and get response
        self.logger.debug("get_outlet_in_use")

        # Dispatch event from HAP thread (thread-safe)
        self.event_bus.dispatch(
            OutletGetInUseEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        return self.is_in_use

    def set_on(self, value: bool) -> None:
        """Set the on/off state of the outlet.

        Args:
            value: True to turn on, False to turn off.
        """
        # Emit set event
        self.logger.debug(f"set_on {value} {self.is_on}")

        self.is_on = value
        self.event_bus.dispatch(
            OutletSetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                value=value,
            )
        )

    def get_on(self) -> bool:
        """Get the on/off state of the outlet.

        Returns:
            True if on, False if off.
        """
        # Emit event and get response
        self.logger.debug("get_on")

        # Dispatch event from HAP thread (thread-safe)
        self.event_bus.dispatch(
            OutletGetOnEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
            )
        )
        return self.is_on
