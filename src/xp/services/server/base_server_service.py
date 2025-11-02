"""Base Server Service with shared functionality.

This module provides a base class for all XP device server services,
containing common functionality like module type response generation.
"""

import logging
import threading
from abc import ABC
from typing import Any, Optional

from xp.models import ModuleTypeCode
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.utils.checksum import calculate_checksum


class BaseServerService(ABC):
    """
    Base class for all XP device server services.

    Provides common functionality that is shared across all device types,
    such as module type response generation.
    """

    def __init__(self, serial_number: str):
        """Initialize base server service.

        Args:
            serial_number: The device serial number.
        """
        self.serial_number = serial_number
        self.logger = logging.getLogger(__name__)

        # Must be set by subclasses
        self.device_type: str = ""
        self.module_type_code: ModuleTypeCode = ModuleTypeCode.NOMOD
        self.hardware_version: str = ""
        self.software_version: str = ""
        self.device_status: str = "OK"
        self.link_number: int = 1
        self.temperature: str = "+23,5§C"
        self.voltage: str = "+12,5§V"

        self.telegram_buffer: list[str] = []
        self.telegram_buffer_lock = threading.Lock()  # Lock for socket set

        # MsActionTable download state (None, "ack_sent", "data_sent")
        self.msactiontable_download_state: Optional[str] = None

    def generate_datapoint_type_response(
        self, datapoint_type: DataPointType
    ) -> Optional[str]:
        """Generate datapoint_type response telegram.

        Args:
            datapoint_type: The type of datapoint to query.

        Returns:
            The response telegram string, or None if generation fails.
        """
        datapoint_values = {
            DataPointType.TEMPERATURE: self.temperature,
            DataPointType.MODULE_TYPE_CODE: f"{self.module_type_code.value:02}",
            DataPointType.SW_VERSION: self.software_version,
            DataPointType.MODULE_STATE: self.device_status,
            DataPointType.MODULE_TYPE: self.device_type,
            DataPointType.LINK_NUMBER: f"{self.link_number:02}",
            DataPointType.VOLTAGE: self.voltage,
            DataPointType.HW_VERSION: self.hardware_version,
            DataPointType.MODULE_ERROR_CODE: "00",
        }
        data_value = datapoint_values.get(datapoint_type) or "00"
        data_part = f"R{self.serial_number}F02D{datapoint_type.value}{data_value}"
        telegram = self._build_response_telegram(data_part)

        self.logger.debug(
            f"Generated {self.device_type} module type response: {telegram}"
        )
        return telegram

    def _check_request_for_device(self, request: SystemTelegram) -> bool:
        """Check if request is for this device (including broadcast).

        Args:
            request: The system telegram request to check.

        Returns:
            True if request is for this device or broadcast, False otherwise.
        """
        return request.serial_number in (self.serial_number, "0000000000")

    @staticmethod
    def _build_response_telegram(data_part: str) -> str:
        """Build a complete response telegram with checksum.

        Args:
            data_part: The data part of the telegram without checksum.

        Returns:
            The complete telegram with checksum enclosed in angle brackets.
        """
        checksum = calculate_checksum(data_part)
        return f"<{data_part}{checksum}>"

    def _log_response(self, response_type: str, telegram: str) -> None:
        """Log response generation.

        Args:
            response_type: The type of response being generated.
            telegram: The telegram string being logged.
        """
        self.logger.debug(
            f"Generated {self.device_type} {response_type} response: {telegram}"
        )

    def generate_discover_response(self) -> str:
        """Generate discover response telegram.

        Returns:
            The discover response telegram string.
        """
        data_part = f"R{self.serial_number}F01D"
        telegram = self._build_response_telegram(data_part)
        self._log_response("discover", telegram)
        return telegram

    def set_link_number(
        self, request: SystemTelegram, new_link_number: int
    ) -> Optional[str]:
        """Set link number and generate ACK response.

        Args:
            request: The system telegram request.
            new_link_number: The new link number to set.

        Returns:
            The ACK response telegram string, or None if request is invalid.
        """
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

    def _get_msactiontable_serializer(self) -> Optional[Any]:
        """Get the MsActionTable serializer for this device.

        Subclasses should override this to return their specific serializer.

        Returns:
            The serializer instance, or None if not supported.
        """
        return None

    def _get_msactiontable(self) -> Optional[Any]:
        """Get the MsActionTable for this device.

        Subclasses should override this to return their msactiontable instance.

        Returns:
            The msactiontable instance, or None if not supported.
        """
        return None

    def _handle_download_msactiontable_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Handle F13D - DOWNLOAD_MSACTIONTABLE request.

        Args:
            request: The system telegram request to process.

        Returns:
            ACK telegram if request is valid, NAK otherwise.
        """
        serializer = self._get_msactiontable_serializer()
        msactiontable = self._get_msactiontable()

        # Only handle if serializer and msactiontable are available
        if not serializer or msactiontable is None:
            return None

        # Send ACK and queue data telegram
        ack_data = self._build_response_telegram(f"R{self.serial_number}F18D")  # ACK

        # Send MsActionTable data
        encoded_data = serializer.to_data(msactiontable)
        data_telegram = self._build_response_telegram(
            f"R{self.serial_number}F17D{encoded_data}"
        )
        self.msactiontable_download_state = "data_sent"

        # Return ACK and TABLE
        return ack_data + data_telegram

    def _handle_download_msactiontable_ack_request(
        self, _request: SystemTelegram
    ) -> Optional[str]:
        """Handle MsActionTable download ACK protocol.

        Args:
            _request: The system telegram request (unused, kept for signature consistency).

        Returns:
            Data telegram, EOF telegram, or NAK if state is invalid.
        """
        if self.msactiontable_download_state == "data_sent":
            # Send EOF
            eof_telegram = self._build_response_telegram(f"R{self.serial_number}F16D")
            self.msactiontable_download_state = None
            return eof_telegram

        return self._build_response_telegram(f"R{self.serial_number}F19D")  # NAK

    def process_system_telegram(self, request: SystemTelegram) -> Optional[str]:
        """Template method for processing system telegrams.

        Args:
            request: The system telegram request to process.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
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

        elif request.system_function == SystemFunction.DOWNLOAD_MSACTIONTABLE:
            return self._handle_download_msactiontable_request(request)

        elif (
            request.system_function == SystemFunction.ACK
            and self.msactiontable_download_state
        ):
            return self._handle_download_msactiontable_ack_request(request)

        self.logger.warning(f"Unhandled {self.device_type} request: {request}")
        return None

    def _handle_return_data_request(self, request: SystemTelegram) -> Optional[str]:
        """Handle RETURN_DATA requests - can be overridden by subclasses.

        Args:
            request: The system telegram request.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        self.logger.debug(
            f"_handle_return_data_request {self.device_type} request: {request}"
        )
        module_specific = self._handle_device_specific_data_request(request)
        if module_specific:
            return module_specific

        if request.datapoint_type:
            return self.generate_datapoint_type_response(request.datapoint_type)

        # Allow device-specific handlers
        return None

    def _handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Override in subclasses for device-specific data requests.

        Args:
            request: The system telegram request.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        return None

    def _handle_write_config_request(self, request: SystemTelegram) -> Optional[str]:
        """Handle WRITE_CONFIG requests.

        Args:
            request: The system telegram request.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        if request.datapoint_type == DataPointType.LINK_NUMBER:
            return self.set_link_number(request, 1)  # Default implementation

        return self._handle_device_specific_config_request()

    def _handle_action_request(self, request: SystemTelegram) -> Optional[str]:
        """Handle ACTION requests.

        Args:
            request: The system telegram request.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        return self._handle_device_specific_action_request(request)

    def _handle_device_specific_action_request(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Override in subclasses for device-specific data requests.

        Args:
            request: The system telegram request.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        return None

    @staticmethod
    def _handle_device_specific_config_request() -> Optional[str]:
        """Override in subclasses for device-specific config requests.

        Returns:
            The response telegram string, or None if request cannot be handled.
        """
        return None

    def add_telegram_buffer(self, telegram: str) -> None:
        """Add telegram to the buffer.

        Args:
            telegram: The telegram string to add to the buffer.
        """
        self.logger.debug(f"Add telegram to the buffer: {telegram}")
        with self.telegram_buffer_lock:
            self.telegram_buffer.append(telegram)

    def collect_telegram_buffer(self) -> list[str]:
        """Collecting telegrams from the buffer.

        Returns:
            List of telegram strings from the buffer. The buffer is cleared after collection.
        """
        with self.telegram_buffer_lock:
            result = self.telegram_buffer.copy()
            self.telegram_buffer.clear()
            return result
