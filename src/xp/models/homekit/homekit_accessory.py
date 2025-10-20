"""HomeKit configuration models."""

import random
from typing import Any

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR


class TemperatureSensor(Accessory):
    """Fake Temperature sensor, measuring every 3 seconds.

    Attributes:
        category: HomeKit category for sensor.
        char_temp: Temperature characteristic.
    """

    category = CATEGORY_SENSOR

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize temperature sensor accessory.

        Args:
            args: Positional arguments passed to parent Accessory.
            kwargs: Keyword arguments passed to parent Accessory.
        """
        super().__init__(*args, **kwargs)

        serv_temp = self.add_preload_service("TemperatureSensor")
        self.char_temp = serv_temp.configure_char("CurrentTemperature")

    @Accessory.run_at_interval(30)
    async def run(self) -> None:
        """Update temperature value every 30 seconds."""
        self.char_temp.set_value(random.randint(-25, 25))
