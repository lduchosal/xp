from enum import Enum


class InputType(Enum):
    """Input types based on input number ranges"""

    PUSH_BUTTON = "push_button"  # Input 00-09
    IR_REMOTE = "ir_remote"  # Input 10-89
    PROXIMITY_SENSOR = "proximity_sensor"  # Input 90
