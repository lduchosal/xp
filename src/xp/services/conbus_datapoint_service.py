"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging

from .conbus_service import ConbusService
from ..models import (
    ConbusDatapointResponse,
)
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from ..services.telegram_service import TelegramService


class ConbusDatapointError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusDatapointService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus client send service"""

        # Service dependencies
        self.telegram_service = TelegramService()
        self.conbus_service = ConbusService(config_path)

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def send_telegram(self, datapoint_type: DataPointType, serial_number: str) -> ConbusDatapointResponse:
        """Send a telegram to the Conbus server"""

        system_function = SystemFunction.READ_DATAPOINT
        datapoint_code = datapoint_type.value

        # Send telegram
        response = self.conbus_service.send_telegram(serial_number, system_function, datapoint_code)
        datapoint_telegram = None
        if len(response.received_telegrams) > 0:
            telegram = response.received_telegrams[0]
            datapoint_telegram = self.telegram_service.parse_telegram(telegram)

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      # Cleanup logic if needed
        pass

