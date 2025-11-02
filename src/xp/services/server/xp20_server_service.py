"""XP20 Server Service for device emulation.

This service provides XP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional

from xp.models import ModuleTypeCode
from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
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
        _variant: str,
        msactiontable_serializer: Optional[Xp20MsActionTableSerializer] = None,
    ):
        """Initialize XP20 server service.

        Args:
            serial_number: The device serial number.
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
        self.msactiontable_download_state: Optional[str] = (
            None  # Track: "ack_sent", "data_sent", None
        )

    def _get_default_msactiontable(self) -> Xp20MsActionTable:
        """Generate default MsActionTable configuration.

        Returns:
            Default XP20 MsActionTable with all inputs unconfigured.
        """
        # All inputs unconfigured (all flags False, AND functions empty)
        return Xp20MsActionTable()

    def process_system_telegram(self, request: SystemTelegram) -> Optional[str]:
        """Process system telegrams including MsActionTable download.

        Args:
            request: The system telegram request to process.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        # Check if request is for this device
        if not self._check_request_for_device(request):
            return None

        # Handle F13D - DOWNLOAD_MSACTIONTABLE request
        if request.system_function == SystemFunction.DOWNLOAD_MSACTIONTABLE:
            self.msactiontable_download_state = "ack_sent"
            # Send ACK and queue data telegram
            ack_telegram = self._build_response_telegram(f"R{self.serial_number}F18D")
            self.add_telegram_buffer(ack_telegram)
            return None  # ACK sent via buffer

        # Handle F18D - CONTINUE (after ACK or data)
        if (
            request.system_function == SystemFunction.ACK
            and self.msactiontable_download_state
        ):
            if self.msactiontable_download_state == "ack_sent":
                # Send MsActionTable data
                encoded_data = self.msactiontable_serializer.to_data(self.msactiontable)
                data_telegram = self._build_response_telegram(
                    f"R{self.serial_number}F17D{encoded_data}"
                )
                self.add_telegram_buffer(data_telegram)
                self.msactiontable_download_state = "data_sent"
                return None

            elif self.msactiontable_download_state == "data_sent":
                # Send EOF
                eof_telegram = self._build_response_telegram(
                    f"R{self.serial_number}F16D"
                )
                self.add_telegram_buffer(eof_telegram)
                self.msactiontable_download_state = None
                return None

        # Delegate to base class for other requests
        return super().process_system_telegram(request)

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
