"""Base Server Service with shared functionality.

This module provides a base class for all XP device server services,
containing common functionality like module type response generation.
"""

import logging
from typing import Optional
from abc import ABC

from ..models.system_telegram import SystemTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from ..utils.checksum import calculate_checksum


class BaseServerService(ABC):
    """
    Base class for all XP device server services.

    Provides common functionality that is shared across all device types,
    such as module type response generation.
    """

    def __init__(self, serial_number: str):
        """Initialize base server service"""
        self.serial_number = serial_number
        self.logger = logging.getLogger(__name__)

        # Must be set by subclasses
        self.device_type: str = ""
        self.module_type_code: int = 0
        self.hardware_version: str = ""
        self.software_version: str = ""
        self.device_status: str = "OK"
        self.link_number: int = 1
        self.temperature: str = "+23,5§C"
        self.voltage: str = "+12,5§V"

    def generate_datapoint_type_response(
        self, datapoint_type: DataPointType
    ) -> Optional[str]:
        """Generate datapoint_type response telegram"""
        datapoint_values = {
            DataPointType.TEMPERATURE: self.temperature,
            DataPointType.MODULE_TYPE_CODE: f"{self.module_type_code:02X}",
            DataPointType.SW_VERSION: self.software_version,
            DataPointType.ERROR_CODE: self.device_status,
            DataPointType.LINK_NUMBER: f"{self.link_number:02X}",
            DataPointType.VOLTAGE: self.voltage,
            DataPointType.HW_VERSION: self.hardware_version,
        }
        data_part = f"R{self.serial_number}F02{datapoint_type.value}{self.module_type_code}{datapoint_values.get(datapoint_type)}"
        telegram = self._build_response_telegram(data_part)

        self.logger.debug(
            f"Generated {self.device_type} module type response: {telegram}"
        )
        return telegram

    def _check_request_for_device(self, request: SystemTelegram) -> bool:
        """Check if request is for this device (including broadcast)"""
        return request.serial_number in (self.serial_number, "0000000000")

    @staticmethod
    def _build_response_telegram(data_part: str) -> str:
        """Build a complete response telegram with checksum"""
        checksum = calculate_checksum(data_part)
        return f"<{data_part}{checksum}>"

    def _log_response(self, response_type: str, telegram: str) -> None:
        """Log response generation"""
        self.logger.debug(
            f"Generated {self.device_type} {response_type} response: {telegram}"
        )

    def generate_discover_response(self) -> str:
        """Generate discover response telegram"""
        data_part = f"R{self.serial_number}F01D"
        telegram = self._build_response_telegram(data_part)
        self._log_response("discover", telegram)
        return telegram

    def set_link_number(
        self, request: SystemTelegram, new_link_number: int
    ) -> Optional[str]:
        """Set link number and generate ACK response"""
        if (
            request.system_function == SystemFunction.WRITE_CONFIG
            and request.datapoint_type == DataPointType.LINK_NUMBER
        ):
            # Update internal link number
            self.link_number = new_link_number

            # Generate ACK response
            data_part = f"R{self.serial_number}F18D"
            telegram = self._build_response_telegram(data_part)

            self.logger.info(f"{self.device_type} link number set to {new_link_number}")
            return telegram

        return None

    def process_system_telegram(self, request: SystemTelegram) -> Optional[str]:
        """Template method for processing system telegrams"""
        # Check if request is for this device
        if not self._check_request_for_device(request):
            return None

        # Handle different system functions
        if request.system_function == SystemFunction.DISCOVERY:
            return self.generate_discover_response()

        elif request.system_function == SystemFunction.READ_DATAPOINT:
            return self._handle_return_data_request(request)

        elif request.system_function == SystemFunction.WRITE_CONFIG:
            return self._handle_write_config_request(request)

        elif request.system_function == SystemFunction.ACTION:
            return self._handle_action_request(request)

        self.logger.warning(f"Unhandled {self.device_type} request: {request}")
        return None

    def _handle_return_data_request(self, request: SystemTelegram) -> Optional[str]:
        """Handle RETURN_DATA requests - can be overridden by subclasses"""
        self.logger.warning(
            f"_handle_return_data_request {self.device_type} request: {request}"
        )
        if request.datapoint_type:
            return self.generate_datapoint_type_response(request.datapoint_type)

        # Allow device-specific handlers
        return self._handle_device_specific_data_request(request)

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Override in subclasses for device-specific data requests"""
        return None

    def _handle_write_config_request(self, request: SystemTelegram) -> Optional[str]:
        """Handle WRITE_CONFIG requests"""
        if request.datapoint_type == DataPointType.LINK_NUMBER:
            return self.set_link_number(request, 1)  # Default implementation

        return self._handle_device_specific_config_request()

    def _handle_action_request(self, request: SystemTelegram) -> Optional[str]:
        """Handle ACTION requests"""
        return self._handle_device_specific_action_request(request)

    def _handle_device_specific_action_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Override in subclasses for device-specific data requests"""
        return None

    @staticmethod
    def _handle_device_specific_config_request() -> Optional[str]:
        """Override in subclasses for device-specific config requests"""
        return None
