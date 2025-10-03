"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from xp.models import ConbusDatapointResponse
from xp.models.conbus.conbus_output import ConbusOutputResponse
from xp.models.telegram.action_type import ActionType
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.conbus_service import ConbusService
from xp.services.telegram.telegram_output_service import TelegramOutputService
from xp.services.telegram.telegram_service import TelegramService


class ConbusOutputError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusOutputService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        telegram_output_service: TelegramOutputService,
        datapoint_service: ConbusDatapointService,
        conbus_service: ConbusService,
    ):
        """Initialize the Conbus client send service

        Args:
            telegram_service: TelegramService for dependency injection
            telegram_output_service: TelegramOutputService for dependency injection
            datapoint_service: ConbusDatapointService for dependency injection
            conbus_service: ConbusService for dependency injection
        """

        # Service dependencies
        self.telegram_service = telegram_service
        self.telegram_output_service = telegram_output_service
        self.datapoint_service = datapoint_service
        self.conbus_service = conbus_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> "ConbusOutputService":
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        # Cleanup logic if needed
        pass

    def get_output_state(self, serial_number: str) -> ConbusDatapointResponse:

        # Send status query using custom telegram method
        response = self.datapoint_service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,  # "12"
        )

        return response

    def get_module_state(self, serial_number: str) -> ConbusDatapointResponse:

        # Send status query using custom telegram method
        response = self.datapoint_service.query_datapoint(
            serial_number=serial_number, datapoint_type=DataPointType.MODULE_STATE
        )

        return response

    def send_action(
        self, serial_number: str, output_number: int, action_type: ActionType
    ) -> ConbusOutputResponse:

        # Parse input number and send action
        self.telegram_output_service.validate_output_number(output_number)

        # Send action telegram using custom telegram method
        # Format: F27D{input:02d}AA (Function 27, input number, PRESS action)
        action_value = action_type.value

        input_action = f"{output_number:02d}{action_value}"
        response = self.conbus_service.send_telegram(
            serial_number,
            SystemFunction.ACTION,  # "27"
            input_action,  # "00AA", "01AA", etc.
        )

        if (
            not response.success
            or response.received_telegrams is None
            or len(response.received_telegrams) <= 0
        ):

            return ConbusOutputResponse(
                success=response.success,
                serial_number=serial_number,
                output_number=output_number,
                action_type=action_type,
                error=response.error,
                timestamp=response.timestamp or datetime.now(),
                received_telegrams=response.received_telegrams,
            )

        telegram = response.received_telegrams[0]
        output_telegram = self.telegram_output_service.parse_reply_telegram(telegram)

        return ConbusOutputResponse(
            success=response.success,
            serial_number=serial_number,
            output_number=output_number,
            action_type=action_type,
            output_telegram=output_telegram,
            timestamp=response.timestamp or datetime.now(),
            received_telegrams=response.received_telegrams,
        )
