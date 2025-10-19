"""Input type enumeration based on input number ranges."""

from enum import Enum


class InputType(Enum):
    """Input types based on input number ranges.

    Attributes:
        PUSH_BUTTON: Push button input (range 00-09).
        IR_REMOTE: IR remote input (range 10-89).
        PROXIMITY_SENSOR: Proximity sensor input (input 90).
    """

    PUSH_BUTTON = "push_button"  # Input 00-09
    IR_REMOTE = "ir_remote"  # Input 10-89
    PROXIMITY_SENSOR = "proximity_sensor"  # Input 90
