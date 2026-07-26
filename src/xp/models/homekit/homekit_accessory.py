# Copyright (c) 2025 ldvchosal
"""HomeKit configuration models."""

import secrets

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR

# Simulated temperature range in degrees Celsius
MIN_TEMPERATURE = -25
MAX_TEMPERATURE = 25


class TemperatureSensor(Accessory):
    """Fake Temperature sensor, measuring every 3 seconds.

    Attributes:
        category: HomeKit category for sensor.
        char_temp: Temperature characteristic.

    """

    category = CATEGORY_SENSOR

    def __init__(self, *args: object, **kwargs: object) -> None:
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
        span = MAX_TEMPERATURE - MIN_TEMPERATURE + 1
        self.char_temp.set_value(MIN_TEMPERATURE + secrets.randbelow(span))
