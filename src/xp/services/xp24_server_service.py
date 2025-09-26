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

    def generate_temperature_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate temperature response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.TEMPERATURE
        ):
            # Simulate temperature reading: +23.5°C
            temperature_value = "+23,5§C"
            data_part = f"R{self.serial_number}F02D18{temperature_value}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("temperature", telegram)
            return telegram

        return None

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP24-specific data requests"""
        if request.system_function != SystemFunction.READ_DATAPOINT:
            return None

        if request.datapoint_type == DataPointType.TEMPERATURE:
            return self.generate_temperature_response(request)
        if request.datapoint_type == DataPointType.MODULE_OUTPUT_STATE:
            return self.generate_module_output_state_response(request)
        if request.datapoint_type == DataPointType.MODULE_STATE:
            return self.generate_module_state_response(request)

        return None

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

    def generate_module_output_state_response(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Generate module output state response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        ):
            module_output_state = "xxxx0001"
            data_part = f"R{self.serial_number}F02D12{module_output_state}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("module_output_state", telegram)
            return telegram

        return None

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

    def generate_module_state_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate module output state response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.MODULE_STATE
        ):
            module_state = "OFF"  # ON
            data_part = f"R{self.serial_number}F02D09{module_state}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("module_output_state", telegram)
            return telegram

        return None
