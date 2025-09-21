import logging

from pydispatch import dispatcher
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from xp.utils import get_first_response


class LightBulb(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB

    def __init__(
            self,
            driver: AccessoryDriver,
            display_name: str,
            version: str,
            manufacturer: str,
            model: str,
            serial_number: str,
            output_number: int
        ):
        super().__init__(driver, display_name)

        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating lightbulb { serial_number : %s, output_number: %s }", serial_number, output_number)

        self.serial_number = serial_number
        self.output_number = output_number
        serial = f"{serial_number}.{output_number:02d}"

        serv_light = self.add_preload_service('Lightbulb') # type: ignore
        self.set_info_service(
            version,
            manufacturer,
            model,
            serial)

        self.char_on = serv_light.configure_char(
            'On',
            getter_callback=self.get_on,
            setter_callback=self.set_on
        )

    def set_on(self, value):
        # Emit event using PyDispatcher
        dispatcher.send(
            signal='accessory_set_on',
            sender=self,
            serial_number=self.serial_number,
            output_number=self.output_number,
            value=value,
        )

    def get_on(self) -> bool:
        # Emit event and get response
        responses = dispatcher.send(
            signal='accessory_get_on',
            sender=self,
            serial_number=self.serial_number,
            output_number=self.output_number,
        )
        # Return first response or default to True
        response = get_first_response(responses)
        return response
