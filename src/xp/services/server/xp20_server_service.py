"""XP20 Server Service for device emulation.

This service provides XP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict
from .base_server_service import BaseServerService


class XP20ServerError(Exception):
    """Raised when XP20 server operations fail"""

    pass


class XP20ServerService(BaseServerService):
    """
    XP20 device emulation service.

    Generates XP20-specific responses, handles XP20 device configuration,
    and implements XP20 telegram format.
    """

    def __init__(self, serial_number: str):
        """Initialize XP20 server service"""
        super().__init__(serial_number)
        self.device_type = "XP20"
        self.module_type_code = 33  # XP20 module type from registry
        self.firmware_version = "XP20_V0.01.05"

    def get_device_info(self) -> Dict:
        """Get XP20 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }
