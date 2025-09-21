import random
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_LIGHTBULB, CATEGORY_OUTLET
import logging

class Outlet(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_OUTLET

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logging.getLogger(__name__)

        serv_outlet = self.add_preload_service('Outlet') # type: ignore
        self.char_on = serv_outlet.configure_char('On', setter_callback=self.set_on)
        self.char_outlet_in_use = serv_outlet.configure_char('OutletInUse', setter_callback=self.set_outlet_in_use)

    def set_on(self, value):
        self.logger.info("Outlet on: %s", value)

    def set_outlet_in_use(self, value):
        self.logger.info("Outlet in use: %s", value)


class LightBulb(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logging.getLogger(__name__)

        serv_light = self.add_preload_service('Lightbulb') # type: ignore
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_on)

    def set_on(self, value):
        self.logger.info("Bulb on: %s", value)


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
