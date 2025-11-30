"""Module state data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ModuleState:
    """
    State of a Conson module for TUI display.

    Attributes:
        name: Module name/identifier (e.g., A01, A02).
        serial_number: Module serial number.
        module_type: Module type designation (e.g., XP130, XP230, XP24).
        link_number: Link number for the module.
        outputs: Output states as space-separated binary values. Empty string for modules without outputs.
        auto_report: Auto-report enabled status (Y/N).
        error_status: Module status ("OK" or error code like "E10").
        last_update: Last communication timestamp. None if never updated.
    """

    name: str
    serial_number: str
    module_type: str
    link_number: int
    outputs: str
    auto_report: bool
    error_status: str
    last_update: Optional[datetime]
