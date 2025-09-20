"""XP20 Server Service for device emulation.

This service provides XP20-specific device emulation functionality,
including response generation and device configuration handling.
"""

from typing import Dict, Optional
from ..models.system_telegram import SystemTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from .base_server_service import BaseServerService


class XP20ServerError(Exception):
    """Raised when XP20 server operations fail"""

    pass


class XP20ServerService(BaseServerService):
    """
    XP20 device emulation service.

    Generates XP20-specific responses, handles XP20 device configuration,
    and implements XP20 telegram format.
    """

    def __init__(self, serial_number: str):
        """Initialize XP20 server service"""
        super().__init__(serial_number)
        self.device_type = "XP20"
        self.module_type_code = 33  # XP20 module type from registry
        self.firmware_version = "XP20_V0.01.05"

    def generate_humidity_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate humidity response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.SW_TOP_VERSION
        ):
            # Simulate humidity reading: +65.5%RH
            humidity_value = "+65,5§RH"
            data_part = f"R{self.serial_number}F02D19{humidity_value}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("humidity", telegram)
            return telegram

        return None

    def generate_voltage_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate voltage response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.VOLTAGE
        ):
            # Simulate voltage reading: +12.5V
            voltage_value = "+12,5§V"
            data_part = f"R{self.serial_number}F02D20{voltage_value}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("voltage", telegram)
            return telegram

        return None

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP20-specific data requests"""
        if request.datapoint_type == DataPointType.SW_TOP_VERSION:
            return self.generate_humidity_response(request)
        elif request.datapoint_type == DataPointType.VOLTAGE:
            return self.generate_voltage_response(request)

        return None

    def get_device_info(self) -> Dict:
        """Get XP20 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number,
        }
