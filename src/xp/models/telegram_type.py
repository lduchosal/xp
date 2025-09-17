from enum import Enum


class TelegramType(Enum):
    """Supported telegram types for Conbus client send operations"""

    DISCOVERY = "discovery"
    VERSION = "version"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    HUMIDITY = "humidity"
    BLINK = "blink"
    UNBLINK = "unblink"

