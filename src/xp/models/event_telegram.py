from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional
from .module_type import ModuleType
from .telegram import Telegram


class EventType(Enum):
    """Event types for telegraph events"""
    BUTTON_PRESS = "M"  # Make
    BUTTON_RELEASE = "B"  # Break


class InputType(Enum):
    """Input types based on input number ranges"""
    PUSH_BUTTON = "push_button"  # Input 00-09
    IR_REMOTE = "ir_remote"      # Input 10-89
    PROXIMITY_SENSOR = "proximity_sensor"  # Input 90

@dataclass
class EventTelegram(Telegram):
    """
    Represents a parsed event telegram from the console bus.
    
    Format: <E{module_type}L{link_number}I{input_number}{event_type}{checksum}>
    Example: <E14L00I02MAK>
    """
    module_type: int = 0
    link_number: int = 0
    input_number: int = 0
    event_type: Optional[EventType] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def module_info(self) -> Optional[ModuleType]:
        """Get module type information for this telegram"""
        return ModuleType.from_code(self.module_type)
    
    @property
    def input_type(self) -> InputType:
        """Determines the input type based on input number"""
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
        """True if this is a button press event"""
        return self.event_type == EventType.BUTTON_PRESS
    
    @property
    def is_button_release(self) -> bool:
        """True if this is a button release event"""
        return self.event_type == EventType.BUTTON_RELEASE
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        result = {
            "module_type": self.module_type,
            "link_number": self.link_number,
            "input_number": self.input_number,
            "event_type": self.event_type.value,
            "event_type_name": "button_press" if self.is_button_press else "button_release",
            "input_type": self.input_type.value,
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        
        # Add module information if available
        if self.module_info:
            result["module_info"] = {
                "name": self.module_info.name,
                "description": self.module_info.description,
                "category": self.module_info.category
            }
        else:
            result["module_info"] = None
            
        return result
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        event_desc = "pressed" if self.is_button_press else "released"
        
        # Include module name if available
        module_desc = f"Module {self.module_type}"
        if self.module_info:
            module_desc = f"{self.module_info.name} (Type {self.module_type})"
        
        return (
            f"{module_desc} Link {self.link_number:02d} "
            f"Input {self.input_number:02d} ({self.input_type.value}) {event_desc}"
        )