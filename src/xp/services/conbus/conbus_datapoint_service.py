"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
from typing import Dict, List, Optional

from xp.models import (
    ConbusDatapointResponse,
)
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.services.conbus.conbus_service import ConbusService
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService


class ConbusDatapointError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusDatapointService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        conbus_service: ConbusService,
    ):
        """Initialize the Conbus client send service

        Args:
            telegram_service: TelegramService for dependency injection
            conbus_service: ConbusService for dependency injection
        """

        # Service dependencies
        self.telegram_service = telegram_service
        self.conbus_service = conbus_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def query_datapoint(
        self, datapoint_type: DataPointType, serial_number: str
    ) -> ConbusDatapointResponse:
        """Send a telegram to the Conbus server"""

        system_function = SystemFunction.READ_DATAPOINT
        datapoint_code = datapoint_type.value

        # Send telegram
        response = self.conbus_service.send_telegram(
            serial_number, system_function, datapoint_code
        )
        datapoint_telegram: Optional[ReplyTelegram] = None
        if (
            response.received_telegrams is not None
            and len(response.received_telegrams) > 0
        ):
            telegram = response.received_telegrams[0]
            try:
                datapoint_telegram = self.telegram_service.parse_reply_telegram(
                    telegram
                )
            except TelegramParsingError as e:
                self.logger.debug(f"Not a reply telegram {e}")

        return ConbusDatapointResponse(
            success=response.success,
            serial_number=serial_number,
            system_function=system_function,
            datapoint_type=datapoint_type,
            sent_telegram=response.sent_telegram,
            received_telegrams=response.received_telegrams,
            datapoint_telegram=datapoint_telegram,
            error=response.error,
        )

    def query_all_datapoints(self, serial_number: str) -> ConbusDatapointResponse:
        """Query all available datapoints for a given serial number"""

        datapoints: List[Dict[str, str]] = []
        has_any_success = False
        last_error = None

        # Query each datapoint type
        for datapoint_type in DataPointType:
            try:
                response = self.query_datapoint(datapoint_type, serial_number)

                if response.success and response.datapoint_telegram:
                    # Extract datapoint name and value
                    datapoint_name = datapoint_type.name
                    datapoint_value = str(response.datapoint_telegram.data_value)
                    datapoints.append({datapoint_name: datapoint_value})
                    has_any_success = True
                elif response.error:
                    last_error = response.error

            except Exception as e:
                self.logger.debug(f"Failed to query datapoint {datapoint_type}: {e}")
                last_error = str(e)
                # Continue with other datapoints even if one fails
                continue

        # If no datapoints were successfully retrieved, return error
        if not has_any_success and last_error:
            return ConbusDatapointResponse(
                success=False,
                serial_number=serial_number,
                system_function=SystemFunction.READ_DATAPOINT,
                error=last_error,
                datapoints=[],
            )

        return ConbusDatapointResponse(
            success=True,
            serial_number=serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            datapoints=datapoints,
        )

    def __enter__(self) -> "ConbusDatapointService":
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object | None,
    ) -> None:
        # Cleanup logic if needed
        pass
