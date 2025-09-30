"""XP24 Server Service for device emulation.

This service provides XP24-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional

from ..models.system_telegram import SystemTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from .base_server_service import BaseServerService


class XP24ServerError(Exception):
    """Raised when XP24 server operations fail"""

    pass


class XP24ServerService(BaseServerService):
    """
    XP24 device emulation service.

    Generates XP24-specific responses, handles XP24 device configuration,
    and implements XP24 telegram format.
    """

    def __init__(self, serial_number: str):
        """Initialize XP24 server service"""
        super().__init__(serial_number)
        self.device_type = "XP24"
        self.module_type_code = 7  # XP24 module type from registry
        self.firmware_version = "XP24_V0.34.03"

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP24-specific data requests"""
        if (
            request.system_function != SystemFunction.READ_DATAPOINT
            or not request.datapoint_type
        ):
            return None

        datapoint_type = request.datapoint_type
        datapoint_values = {
            DataPointType.MODULE_OUTPUT_STATE: "xxxx0001",
            DataPointType.MODULE_STATE: "OFF",
            DataPointType.MODULE_OPERATING_HOURS: "00:000[H],01:000[H],02:000[H],03:000[H]",
        }
        data_part = f"R{self.serial_number}F02{datapoint_type.value}{self.module_type_code}{datapoint_values.get(datapoint_type)}"
        telegram = self._build_response_telegram(data_part)

        self.logger.debug(
            f"Generated {self.device_type} module type response: {telegram}"
        )
        return telegram

    def _handle_device_specific_action_request(
        self, request: SystemTelegram
    ) -> Optional[str]:

        if request.system_function != SystemFunction.ACTION:
            return None

        return self.generate_action_response(request)

    def get_device_info(self) -> Dict:
        """Get XP24 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }

    def generate_action_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate action response telegram (simulated)"""
        response = "F19D"  # NAK
        if (
            request.system_function == SystemFunction.ACTION
            and request.data[:2] in ("00", "01", "02", "03")
            and request.data[2:] in ("AA", "AB")
        ):
            response = "F18D"  # ACK

        data_part = f"R{self.serial_number}{response}"
        telegram = self._build_response_telegram(data_part)
        self._log_response("module_action_response", telegram)
        return telegram
