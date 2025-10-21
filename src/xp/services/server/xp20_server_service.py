"""XP20 Server Service for device emulation.

This service provides XP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict

from xp.models import ModuleTypeCode
from xp.services.server.base_server_service import BaseServerService


class XP20ServerError(Exception):
    """Raised when XP20 server operations fail."""

    pass


class XP20ServerService(BaseServerService):
    """
    XP20 device emulation service.

    Generates XP20-specific responses, handles XP20 device configuration,
    and implements XP20 telegram format.
    """

    def __init__(self, serial_number: str):
        """Initialize XP20 server service.

        Args:
            serial_number: The device serial number.
        """
        super().__init__(serial_number)
        self.device_type = "XP20"
        self.module_type_code = ModuleTypeCode.XP20  # XP20 module type from registry
        self.firmware_version = "XP20_V0.01.05"

    def get_device_info(self) -> Dict:
        """Get XP20 device information.

        Returns:
            Dictionary containing device information.
        """
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }
