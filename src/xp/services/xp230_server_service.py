"""XP230 Server Service for device emulation.

This service provides XP230-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional
from ..models.system_telegram import SystemTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
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

    def generate_temperature_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate temperature response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.TEMPERATURE
        ):
            # Simulate temperature reading: +50.5°C (from ConReport.log)
            temperature_value = "+50,5§C"
            data_part = f"R{self.serial_number}F02D18{temperature_value}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("temperature", telegram)
            return telegram

        return None

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP230-specific data requests"""
        if request.datapoint_type == DataPointType.TEMPERATURE:
            return self.generate_temperature_response(request)

        return None

    def get_device_info(self) -> Dict:
        """Get XP230 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }
