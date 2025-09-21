import logging

from pydispatch import dispatcher
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_OUTLET

from xp.utils import get_first_response


class Outlet(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_OUTLET

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
        self.logger.info("Creating outlet { serial_number : %s, output_number: %s }", serial_number, output_number)

        self.serial_number: str = serial_number
        self.output_number: int = output_number
        serial = f"{serial_number}.{output_number:02d}"
        serv_outlet = self.add_preload_service('Outlet') # type: ignore

        self.set_info_service(
            version,
            manufacturer,
            model,
            serial)

        self.char_on = serv_outlet.configure_char(
            'On',
            setter_callback=self.set_on,
            getter_callback = self.get_on
        )
        self.char_outlet_in_use = serv_outlet.configure_char(
            'OutletInUse',
            setter_callback=self.set_outlet_in_use,
            getter_callback=self.get_outlet_in_use,
        )

    def set_outlet_in_use(self, value):
        dispatcher.send(
            signal='outlet_set_outlet_in_use',
            sender=self,
            serial_number=self.serial_number,
            output_number=self.output_number,
            value=value,
        )

    def get_outlet_in_use(self):
        responses = dispatcher.send(
            signal='outlet_get_outlet_in_use',
            sender=self,
            serial_number=self.serial_number,
            output_number=self.output_number,
        )

        response = get_first_response(responses)
        return response

    def set_on(self, value):
        # Emit event using PyDispatcher
        dispatcher.send(
            signal='accessory_set_on',
            sender=self,
            serial_number=self.serial_number,
            output_number=self.output_number,
            value=value,
        )

    def get_on(self):
        # Emit event and get response
        responses = dispatcher.send(signal='accessory_get_on',
            sender=self,
            serial_number=self.serial_number,
            output_number=self.output_number,
        )
        response = get_first_response(responses)
        return response
