"""XP130 Server Service for device emulation.

This service provides XP130-specific device emulation functionality,
including response generation and device configuration handling.
XP130 is an Ethernet/TCPIP interface module.
"""

from typing import Dict, Optional
from ..models.system_telegram import SystemTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from .base_server_service import BaseServerService


class XP130ServerError(Exception):
    """Raised when XP130 server operations fail"""

    pass


class XP130ServerService(BaseServerService):
    """
    XP130 device emulation service.

    Generates XP130-specific responses, handles XP130 device configuration,
    and implements XP130 telegram format for Ethernet/TCPIP interface module.
    """

    def __init__(self, serial_number: str):
        """Initialize XP130 server service"""
        super().__init__(serial_number)
        self.device_type = "XP130"
        self.module_type_code = 13  # XP130 module type from registry
        self.firmware_version = "XP130_V1.02.15"

        # XP130-specific network configuration
        self.ip_address = "192.168.1.100"
        self.subnet_mask = "255.255.255.0"
        self.gateway = "192.168.1.1"

    def generate_ip_config_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate IP configuration response telegram"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.VOLTAGE
        ):
            # Format: <R{serial}F02D20{ip_config}{checksum}>
            # IP config includes IP, subnet, gateway separated by commas
            ip_config = f"{self.ip_address},{self.subnet_mask},{self.gateway}"
            data_part = f"R{self.serial_number}F02D20{ip_config}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("IP config", telegram)
            return telegram

        return None

    def generate_temperature_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate temperature response telegram (simulated)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.TEMPERATURE
        ):
            # Simulate temperature reading: +21.0°C (network equipment runs cooler)
            temperature_value = "+21,0§C"
            data_part = f"R{self.serial_number}F02D18{temperature_value}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("temperature", telegram)
            return telegram

        return None

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle XP130-specific data requests"""
        if request.datapoint_type == DataPointType.TEMPERATURE:
            return self.generate_temperature_response(request)
        elif request.datapoint_type == DataPointType.VOLTAGE:
            return self.generate_ip_config_response(request)

        return None

    def get_device_info(self) -> Dict:
        """Get XP130 device information"""
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
