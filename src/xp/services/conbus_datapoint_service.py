"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging
from typing import Optional

from .conbus_service import ConbusService
from ..models import (
    ConbusDatapointResponse,
)
from ..models.datapoint_type import DataPointType
from ..models.reply_telegram import ReplyTelegram
from ..models.system_function import SystemFunction
from ..services.telegram_service import TelegramService, TelegramParsingError


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
        datapoint_telegram: Optional[ReplyTelegram] = None
        if response.received_telegrams is not None and len(response.received_telegrams) > 0:
            telegram = response.received_telegrams[0]
            try:
                parsed_telegram = self.telegram_service.parse_reply_telegram(telegram)
                datapoint_telegram = parsed_telegram
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

    def __enter__(self) -> 'ConbusDatapointService':
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None) -> None:
      # Cleanup logic if needed
        pass

