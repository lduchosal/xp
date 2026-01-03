"""Accessory state data model for Homekit TUI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AccessoryState:
    """
    State of a HomeKit accessory for TUI display.

    Attributes:
        room_name: Room containing the accessory (e.g., "Salon").
        accessory_name: Accessory display name (e.g., "Variateur salon").
        action: Action key (a-z0-9) for toggle control.
        output_state: Output state ("ON", "OFF", "?").
        dimming_state: Dimming percentage for dimmable modules, "-" if OFF, empty otherwise.
        module_name: Module identifier (e.g., "A12").
        serial_number: Module serial number.
        module_type: Module type (e.g., "XP24", "XP33LED").
        error_status: Status code ("OK" or error like "E10").
        output: Module output number (1-based for display).
        sort: Sort accessories according to homekit.yml configuration.
        last_update: Last communication timestamp. None if never updated.
        toggle_action: Raw toggle action telegram (e.g., "E02L12I02").
    """

    room_name: str
    accessory_name: str
    action: str
    output_state: str
    dimming_state: str
    module_name: str
    serial_number: str
    module_type: str
    error_status: str
    output: int
    sort: int
    last_update: Optional[datetime] = None
    toggle_action: Optional[str] = None

    def is_dimmable(self) -> bool:
        """
        Check if accessory is dimmable.

        Returns:
            True if module type is XP33LR or XP33LED, False otherwise.
        """
        return self.module_type in ("XP33LR", "XP33LED")
