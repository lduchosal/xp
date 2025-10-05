import asyncio
import logging
from typing import Optional

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
    OutletSetOnEvent, DatapointReceivedEvent,
)
from xp.models.telegram.datapoint_type import DataPointType


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
        self.is_on = False
        self.is_in_use = False
        self.event_bus.on(DatapointReceivedEvent, self.on_datapoint_received)

        serial = f"{module.serial_number}.{accessory.output_number:02d}"
        version = accessory.id
        manufacturer = "Conson"
        model = ("XP24_outlet",)
        serv_outlet = self.add_preload_service("Outlet")
        self.set_info_service(version, manufacturer, model, serial)
        self.char_on = serv_outlet.configure_char(
            "On",
            setter_callback=self.set_on,
            getter_callback=self.get_on
        )
        self.char_outlet_in_use = serv_outlet.configure_char(
            "OutletInUse",
            setter_callback=self.set_outlet_in_use,
            getter_callback=self.get_outlet_in_use,
        )

    def on_datapoint_received(self, event: DatapointReceivedEvent) -> Optional[bool]:

        if (event.serial_number != self.module.serial_number
            or event.datapoint_type != DataPointType.MODULE_OUTPUT_STATE
        ):
            return None

        is_on = event.data_value[::-1][self.accessory.output_number] == "1"
        self.is_on = is_on
        self.is_in_use = is_on
        self.logger.debug(
            f"on_datapoint_received "
            f"serial_number: {event.serial_number}, "
            f"output_number: {self.accessory.output_number}, "
            f"data_vale: {event.data_value}"
            f"is_on: {is_on}"
        )
        return is_on


    def set_outlet_in_use(self, value: bool) -> None:
        self.logger.debug(f"set_outlet_in_use {value}")

        self.is_in_use = value
        self.event_bus.dispatch(
            OutletSetInUseEvent(
                serial_number=self.accessory.serial_number,
                output_number=self.accessory.output_number,
                module=self.module,
                accessory=self.accessory,
                value=value
            )
        )
        self.logger.debug(f"set_outlet_in_use {value} end")

    def get_outlet_in_use(self) -> bool:
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
        # Emit set event
        self.logger.debug(f"set_on {value}")
        self.is_on = value

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
