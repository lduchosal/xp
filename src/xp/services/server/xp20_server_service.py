"""XP20 Server Service for device emulation.

This service provides XP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.services.actiontable.msactiontable_xp20_serializer import (
    Xp20MsActionTableSerializer,
)
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

    def __init__(
        self,
        serial_number: str,
        _variant: str = "",
        msactiontable_serializer: Optional[Xp20MsActionTableSerializer] = None,
    ):
        """Initialize XP20 server service.

        Args:
            serial_number: The device serial number.
            _variant: Reserved parameter for consistency (unused).
            msactiontable_serializer: MsActionTable serializer (injected via DI).
        """
        super().__init__(serial_number)
        self.device_type = "XP20"
        self.module_type_code = ModuleTypeCode.XP20  # XP20 module type from registry
        self.firmware_version = "XP20_V0.01.05"

        # MsActionTable support
        self.msactiontable_serializer = (
            msactiontable_serializer or Xp20MsActionTableSerializer()
        )
        self.msactiontable = self._get_default_msactiontable()

    def _get_msactiontable_serializer(self) -> Optional[Xp20MsActionTableSerializer]:
        """Get the MsActionTable serializer for XP20.

        Returns:
            The XP20 MsActionTable serializer instance.
        """
        return self.msactiontable_serializer

    def _get_msactiontable(self) -> Optional[Xp20MsActionTable]:
        """Get the MsActionTable for XP20.

        Returns:
            The XP20 MsActionTable instance.
        """
        return self.msactiontable

    def _get_default_msactiontable(self) -> Xp20MsActionTable:
        """Generate default MsActionTable configuration.

        Returns:
            Default XP20 MsActionTable with all inputs unconfigured.
        """
        # All inputs unconfigured (all flags False, AND functions empty)
        return Xp20MsActionTable()

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
