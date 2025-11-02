"""XP230 Server Service for device emulation.

This service provides XP230-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.services.actiontable.msactiontable_serializer import MsActionTableSerializer
from xp.services.server.base_server_service import BaseServerService


class XP230ServerError(Exception):
    """Raised when XP230 server operations fail."""

    pass


class XP230ServerService(BaseServerService):
    """
    XP230 device emulation service.

    Generates XP230-specific responses, handles XP230 device configuration,
    and implements XP230 telegram format.
    """

    def __init__(
        self,
        serial_number: str,
        _variant: str = "",
        _msactiontable_serializer: Optional[MsActionTableSerializer] = None,
    ):
        """Initialize XP230 server service.

        Args:
            serial_number: The device serial number.
            _variant: Reserved parameter for consistency (unused).
            _msactiontable_serializer: Generic MsActionTable serializer (unused).
        """
        super().__init__(serial_number)
        self.device_type = "XP230"
        self.module_type_code = ModuleTypeCode.XP230  # XP230 module type from registry
        self.firmware_version = "XP230_V1.00.04"

    def get_device_info(self) -> Dict:
        """Get XP230 device information.

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
