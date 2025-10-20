"""Event telegram model for console bus communication."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from xp.models.telegram.event_type import EventType
from xp.models.telegram.input_type import InputType
from xp.models.telegram.module_type import ModuleType
from xp.models.telegram.telegram import Telegram
from xp.models.telegram.telegram_type import TelegramType


@dataclass
class EventTelegram(Telegram):
    r"""Represent a parsed event telegram from the console bus.

    Format: <[EO]{module_type}L{link_number}I{input_number}{event_type}{checksum}>

    Examples:
        <E14L00I02MAK>

    Attributes:
        event_telegram_type: Event telegram type (E or O).
        module_type: Module type code.
        link_number: Link number.
        input_number: Input number.
        event_type: Type of event (press or release).
        module_info: Module type information if found.
        input_type: Input type based on input number.
        is_button_press: True if this is a button press event.
        is_button_release: True if this is a button release event.
    """

    event_telegram_type: str = "E"  # E or O
    module_type: int = 0
    link_number: int = 0
    input_number: int = 0
    event_type: Optional[EventType] = None

    def __post_init__(self) -> None:
        """Initialize timestamp and telegram type."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.telegram_type = TelegramType.EVENT

    @property
    def module_info(self) -> Optional[ModuleType]:
        """Get module type information for this telegram.

        Returns:
            ModuleType instance if found, None otherwise.
        """
        return ModuleType.from_code(self.module_type)

    @property
    def input_type(self) -> InputType:
        """Determines the input type based on input number.

        Returns:
            InputType enum value.
        """
        if 0 <= self.input_number <= 9:
            return InputType.PUSH_BUTTON
        elif 10 <= self.input_number <= 89:
            return InputType.IR_REMOTE
        elif self.input_number == 90:
            return InputType.PROXIMITY_SENSOR
        else:
            raise ValueError(f"Invalid input number: {self.input_number}")

    @property
    def is_button_press(self) -> bool:
        """True if this is a button press event.

        Returns:
            True if event is a button press, False otherwise.
        """
        return self.event_type == EventType.BUTTON_PRESS

    @property
    def is_button_release(self) -> bool:
        """True if this is a button release event.

        Returns:
            True if event is a button release, False otherwise.
        """
        return self.event_type == EventType.BUTTON_RELEASE

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the event telegram.
        """
        result: dict[str, Any] = {
            "module_type": self.module_type,
            "link_number": self.link_number,
            "output_number": self.input_number,
            "event_type": self.event_type.value if self.event_type else None,
            "event_type_name": (
                "button_press" if self.is_button_press else "button_release"
            ),
            "input_type": self.input_type.value,
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": self.telegram_type.value,
        }

        # Add module information if available
        if self.module_info:
            result["module_info"] = {
                "name": self.module_info.name,
                "description": self.module_info.description,
                "category": self.module_info.category,
            }
        else:
            result["module_info"] = None

        return result

    def __str__(self) -> str:
        """Human-readable string representation.

        Returns:
            Formatted string representation.
        """
        event_desc = "pressed" if self.is_button_press else "released"

        # Include module name if available
        module_desc = f"Module {self.module_type}"
        if self.module_info:
            module_desc = f"{self.module_info.name} (Type {self.module_type})"

        return (
            f"{module_desc} Link {self.link_number:02d} "
            f"Input {self.input_number:02d} ({self.input_type.value}) {event_desc}"
        )
