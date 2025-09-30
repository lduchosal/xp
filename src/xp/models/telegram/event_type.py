from enum import Enum


class EventType(Enum):
    """Event types for telegraph events"""

    BUTTON_PRESS = "M"  # Make
    BUTTON_RELEASE = "B"  # Break
