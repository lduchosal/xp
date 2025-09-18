from enum import Enum


class DatapointTypeName(Enum):
    """Supported telegram types for Conbus client send operations"""

    VERSION = "version"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    HUMIDITY = "humidity"

