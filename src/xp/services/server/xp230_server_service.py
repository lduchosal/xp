"""XP230 Server Service for device emulation.

This service provides XP230-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict
from .base_server_service import BaseServerService


class XP230ServerError(Exception):
    """Raised when XP230 server operations fail"""

    pass


class XP230ServerService(BaseServerService):
    """
    XP230 device emulation service.

    Generates XP230-specific responses, handles XP230 device configuration,
    and implements XP230 telegram format.
    """

    def __init__(self, serial_number: str):
        """Initialize XP230 server service"""
        super().__init__(serial_number)
        self.device_type = "XP230"
        self.module_type_code = 34  # XP230 module type from registry
        self.firmware_version = "XP230_V1.00.04"

    def get_device_info(self) -> Dict:
        """Get XP230 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }
