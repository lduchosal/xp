"""XP130 Server Service for device emulation.

This service provides XP130-specific device emulation functionality,
including response generation and device configuration handling.
XP130 is an Ethernet/TCPIP interface module.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.services.actiontable.msactiontable_serializer import MsActionTableSerializer
from xp.services.server.base_server_service import BaseServerService


class XP130ServerError(Exception):
    """Raised when XP130 server operations fail."""

    pass


class XP130ServerService(BaseServerService):
    """
    XP130 device emulation service.

    Generates XP130-specific responses, handles XP130 device configuration,
    and implements XP130 telegram format for Ethernet/TCPIP interface module.
    """

    def __init__(
        self,
        serial_number: str,
        _variant: str = "",
        _msactiontable_serializer: Optional[MsActionTableSerializer] = None,
    ):
        """Initialize XP130 server service.

        Args:
            serial_number: The device serial number.
            _variant: Reserved parameter for consistency (unused).
            _msactiontable_serializer: Generic MsActionTable serializer (unused).
        """
        super().__init__(serial_number)
        self.device_type = "XP130"
        self.module_type_code = ModuleTypeCode.XP130  # XP130 module type from registry
        self.firmware_version = "XP130_V1.02.15"

        # XP130-specific network configuration
        self.ip_address = "192.168.1.100"
        self.subnet_mask = "255.255.255.0"
        self.gateway = "192.168.1.1"

    def get_device_info(self) -> Dict:
        """Get XP130 device information.

        Returns:
            Dictionary containing device information.
        """
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
            "ip_address": self.ip_address,
            "subnet_mask": self.subnet_mask,
            "gateway": self.gateway,
        }
