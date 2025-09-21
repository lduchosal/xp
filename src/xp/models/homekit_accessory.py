import random
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SENSOR, CATEGORY_LIGHTBULB, CATEGORY_OUTLET
import logging

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
            serial: str,
        ):
        super().__init__(driver, display_name)
        self.logger = logging.getLogger(__name__)

        serv_outlet = self.add_preload_service('Outlet') # type: ignore
        self.set_info_service(
            version,
            manufacturer,
            model,
            serial)

        self.char_on = serv_outlet.configure_char('On', setter_callback=self.set_on)
        self.char_outlet_in_use = serv_outlet.configure_char('OutletInUse', setter_callback=self.set_outlet_in_use)

    def set_on(self, value):
        self.logger.info("Outlet on: %s", value)

    def set_outlet_in_use(self, value):
        self.logger.info("Outlet in use: %s", value)
        return True



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
            serial: str,
        ):
        super().__init__(driver, display_name)

        self.logger = logging.getLogger(__name__)

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
        self.logger.info("Bulb set_on: %s", value)

    def get_on(self, value):
        self.logger.info("Bulb get_on: %s", value)
        return True


class TemperatureSensor(Accessory):
    """Fake Temperature sensor, measuring every 3 seconds."""

    category = CATEGORY_SENSOR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_temp = self.add_preload_service('TemperatureSensor') # type: ignore
        self.char_temp = serv_temp.configure_char('CurrentTemperature')

    @Accessory.run_at_interval(3)
    async def run(self):
        self.char_temp.set_value(random.randint(-25, 25))
