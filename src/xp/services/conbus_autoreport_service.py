"""Conbus Auto Report Service for getting and setting module auto report status.

This service handles auto report status operations for modules through Conbus telegrams.
"""

import logging
from typing import Any, Optional

from . import TelegramService
from .conbus_service import ConbusService
from .conbus_datapoint_service import ConbusDatapointService
from ..models.conbus_autoreport import ConbusAutoreportResponse
from ..models.reply_telegram import ReplyTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from ..utils.checksum import calculate_checksum


class ConbusAutoreportError(Exception):
    """Raised when Conbus autoreport operations fail"""

    pass


def _generate_set_autoreport_telegram(serial_number: str, status_value: str) -> str:
    """
    Generate a telegram for setting auto report status.

    Args:
        serial_number: 10-digit module serial number
        status_value: "PP" for ON, "AA" for OFF

    Returns:
        Formatted telegram string (e.g., "<S0123450001F04E21PPFG>")
    """
    # Build the data part: S{serial_number}F04E21{status_value}
    data_part = f"S{serial_number}F04E21{status_value}"

    # Calculate checksum
    checksum = calculate_checksum(data_part)

    # Build complete telegram
    telegram = f"<{data_part}{checksum}>"

    return telegram


class ConbusAutoreportService:
    """
    Service for getting and setting module auto report status via Conbus telegrams.

    Handles auto report status operations by sending F04E21 telegrams for setting
    and using datapoint queries for getting the current status.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus auto report service"""

        # Service dependencies
        self.conbus_service = ConbusService(config_path)
        self.datapoint_service = ConbusDatapointService(config_path)
        self.telegram_service = TelegramService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> "ConbusAutoreportService":
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        # Cleanup logic if needed
        pass

    def get_autoreport_status(self, serial_number: str) -> ConbusAutoreportResponse:
        """
        Get the current auto report status for a specific module.

        Args:
            serial_number: 10-digit module serial number

        Returns:
            ConbusAutoreportResponse with operation result and auto report status

        Raises:
            ConbusAutoreportError: If the operation fails
        """
        try:
            # Query the AUTO_REPORT_STATUS datapoint
            datapoint_response = self.datapoint_service.query_datapoint(
                DataPointType.AUTO_REPORT_STATUS, serial_number
            )

            if datapoint_response.success and datapoint_response.datapoint_telegram:
                # Extract auto report status from datapoint response
                auto_report_value = datapoint_response.datapoint_telegram.data_value
                return ConbusAutoreportResponse(
                    success=True,
                    serial_number=serial_number,
                    auto_report_status=auto_report_value,
                    sent_telegram=datapoint_response.sent_telegram,
                    received_telegrams=datapoint_response.received_telegrams,
                    timestamp=datapoint_response.timestamp,
                )
            else:
                return ConbusAutoreportResponse(
                    success=False,
                    serial_number=serial_number,
                    sent_telegram=datapoint_response.sent_telegram,
                    received_telegrams=datapoint_response.received_telegrams,
                    error=datapoint_response.error
                    or "Failed to query auto report status",
                    timestamp=datapoint_response.timestamp,
                )

        except Exception as e:
            return ConbusAutoreportResponse(
                success=False,
                serial_number=serial_number,
                error=f"Unexpected error: {e}",
            )

    def set_autoreport_status(
        self, serial_number: str, status: bool
    ) -> ConbusAutoreportResponse:
        """
        Set the auto report status for a specific module.

        Args:
            serial_number: 10-digit module serial number
            status: True for ON, False for OFF

        Returns:
            ConbusAutoreportResponse with operation result

        Raises:
            ConbusAutoreportError: If parameters are invalid
        """
        try:
            # Convert boolean to appropriate value
            status_value = "PP" if status else "AA"
            status_text = "on" if status else "off"

            # Generate the auto report setting telegram: F04E21{value}
            telegram = _generate_set_autoreport_telegram(serial_number, status_value)

            # Send telegram using ConbusService
            with self.conbus_service:
                response = self.conbus_service.send_raw_telegram(telegram)

                # Determine result based on response
                result = "NAK"  # Default to NAK
                if response.success and response.received_telegrams:
                    # Check for ACK response (F18D) or NAK response (F19D)
                    if len(response.received_telegrams) > 0:
                        received_telegram = response.received_telegrams[0]
                        try:
                            parsed_telegram = self.telegram_service.parse_telegram(
                                received_telegram
                            )
                            if isinstance(parsed_telegram, ReplyTelegram):
                                if (
                                    parsed_telegram.system_function
                                    == SystemFunction.ACK
                                ):
                                    result = "ACK"
                                elif (
                                    parsed_telegram.system_function
                                    == SystemFunction.NAK
                                ):
                                    result = "NAK"
                        except Exception as e:
                            self.logger.warning(f"Failed to parse reply telegram: {e}")

                return ConbusAutoreportResponse(
                    success=response.success and result == "ACK",
                    serial_number=serial_number,
                    auto_report_status=status_text,
                    result=result,
                    sent_telegram=telegram,
                    received_telegrams=response.received_telegrams,
                    error=response.error,
                    timestamp=response.timestamp,
                )

        except Exception as e:
            return ConbusAutoreportResponse(
                success=False,
                serial_number=serial_number,
                auto_report_status="off" if not status else "on",
                result="NAK",
                error=f"Unexpected error: {e}",
            )
