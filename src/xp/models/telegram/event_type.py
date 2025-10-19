"""Event type enumeration for telegram events."""

from enum import Enum


class EventType(Enum):
    """Event types for telegraph events.

    Attributes:
        BUTTON_PRESS: Button make (press) event.
        BUTTON_RELEASE: Button break (release) event.
    """

    BUTTON_PRESS = "M"  # Make
    BUTTON_RELEASE = "B"  # Break
