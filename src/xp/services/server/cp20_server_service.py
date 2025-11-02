"""CP20 Server Service for device emulation.

This service provides CP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.actiontable.msactiontable_serializer import MsActionTableSerializer
from xp.services.server.base_server_service import BaseServerService


class CP20ServerError(Exception):
    """Raised when CP20 server operations fail."""

    pass


class CP20ServerService(BaseServerService):
    """
    CP20 device emulation service.

    Generates CP20-specific responses, handles CP20 device configuration,
    and implements CP20 telegram format.
    """

    def __init__(
        self,
        serial_number: str,
        _variant: str = "",
        _msactiontable_serializer: Optional[MsActionTableSerializer] = None,
    ):
        """Initialize CP20 server service.

        Args:
            serial_number: The device serial number.
            _variant: Reserved parameter for consistency (unused).
            _msactiontable_serializer: Generic MsActionTable serializer (unused).
        """
        super().__init__(serial_number)
        self.device_type = "CP20"
        self.module_type_code = ModuleTypeCode.CP20  # CP20 module type from registry
        self.firmware_version = "CP20_V0.01.05"

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle CP20-specific data requests."""
        return None

    def get_device_info(self) -> Dict:
        """Get CP20 device information.

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
