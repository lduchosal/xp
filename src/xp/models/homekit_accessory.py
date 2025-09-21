import random

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR


class TemperatureSensor(Accessory):
    """Fake Temperature sensor, measuring every 3 seconds."""

    category = CATEGORY_SENSOR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_temp = self.add_preload_service('TemperatureSensor') # type: ignore
        self.char_temp = serv_temp.configure_char('CurrentTemperature')

    @Accessory.run_at_interval(30)
    async def run(self):
        self.char_temp.set_value(random.randint(-25, 25))
