"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging

from .conbus_datapoint_service import ConbusDatapointService
from .conbus_service import ConbusService
from .telegram_input_service import TelegramInputService
from ..models import DatapointTypeName, ConbusDatapointResponse
from ..models.action_type import ActionType
from ..models.conbus_input import ConbusInputResponse
from ..models.system_function import SystemFunction
from ..services.telegram_service import TelegramService


class ConbusInputError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusInputService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus client send service"""

        # Service dependencies
        self.telegram_service = TelegramService()
        self.telegram_input_service = TelegramInputService()
        self.datapoint_service = ConbusDatapointService()
        self.conbus_service = ConbusService(config_path)

        # Set up logging
        self.logger = logging.getLogger(__name__)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      # Cleanup logic if needed
        pass

    def send_status(self, serial_number) -> ConbusDatapointResponse:

        # Send status query using custom telegram method
        response = self.datapoint_service.send_datapoint_request(
            serial_number,
            DatapointTypeName.CHANNEL_STATES  # "12"
        )

        return response

    def send_action(self, serial_number:str, input_number:int, action_type:ActionType) -> ConbusInputResponse:

        # Parse input number and send action
        self.telegram_input_service.validate_input_number(input_number)

        # Send action telegram using custom telegram method
        # Format: F27D{input:02d}AA (Function 27, input number, PRESS action)
        action_value = action_type.value

        input_action = f"{input_number:02d}{action_value}"
        response = self.conbus_service.send_telegram(
            serial_number,
            SystemFunction.ACTION,  # "27"
            input_action,  # "00AA", "01AA", etc.
        )

        if not response.success or not len(response.received_telegrams) > 0:
            return ConbusInputResponse(
                success=response.success,
                serial_number=serial_number,
                input_number=input_number,
                action_type=action_type,
                error=response.error,
                timestamp=response.timestamp,
            )

        telegram = response.received_telegrams[0]
        input_telegram = self.telegram_input_service.parse_input_telegram(telegram)

        return ConbusInputResponse(
            success=response.success,
            serial_number=serial_number,
            input_number=input_number,
            action_type=action_type,
            input_telegram=input_telegram,
            timestamp=response.timestamp,
        )
