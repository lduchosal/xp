"""CP20 Server Service for device emulation.

This service provides CP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional
from ..models.system_telegram import SystemTelegram
from .base_server_service import BaseServerService


class CP20ServerError(Exception):
    """Raised when CP20 server operations fail"""

    pass


class CP20ServerService(BaseServerService):
    """
    CP20 device emulation service.

    Generates CP20-specific responses, handles CP20 device configuration,
    and implements CP20 telegram format.
    """

    def __init__(self, serial_number: str):
        """Initialize CP20 server service"""
        super().__init__(serial_number)
        self.device_type = "CP20"
        self.module_type_code = 2  # CP20 module type from registry
        self.firmware_version = "CP20_V0.01.05"

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle CP20-specific data requests"""
        return None

    def get_device_info(self) -> Dict:
        """Get CP20 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }
