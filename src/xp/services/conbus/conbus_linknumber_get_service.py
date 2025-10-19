"""Conbus Link Number Service for setting module link numbers.

This service handles setting link numbers for modules through Conbus telegrams.
"""

import logging
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig, ConbusDatapointResponse
from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.telegram.telegram_service import TelegramService


class ConbusLinknumberGetService(ConbusDatapointService):
    """
    Service for receiving telegrams from Conbus servers.

    Uses composition with ConbusService to provide receive-only functionality
    for collecting waiting event telegrams from the server.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus client send service"""
        super().__init__(telegram_service, cli_config, reactor)
        self.service_callback: Optional[Callable[[ConbusLinknumberResponse], None]] = (
            None
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def finish_service_callback(
        self, datapoint_response: ConbusDatapointResponse
    ) -> None:

        self.logger.debug("Parsing datapoint response")
        link_number_value = 0
        if datapoint_response.success and datapoint_response.datapoint_telegram:
            link_number_value = int(datapoint_response.datapoint_telegram.data_value)

        linknumber_response = ConbusLinknumberResponse(
            success=datapoint_response.success,
            result="SUCCESS" if datapoint_response.success else "FAILURE",
            link_number=link_number_value,
            serial_number=self.serial_number,
            error=datapoint_response.error,
            sent_telegram=datapoint_response.sent_telegram,
            received_telegrams=datapoint_response.received_telegrams,
            timestamp=datapoint_response.timestamp,
        )

        if self.service_callback:
            self.service_callback(linknumber_response)

    def get_linknumber(
        self,
        serial_number: str,
        finish_callback: Callable[[ConbusLinknumberResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Get the current auto report status for a specific module.

        Args:
            :param  serial_number: 10-digit module serial number
            :param  finish_callback: callback function to call when the linknumber status is
            :param  timeout_seconds: timeout in seconds

        """
        self.logger.info("Starting get_linknumber")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.datapoint_type = DataPointType.LINK_NUMBER
        self.finish_callback = self.finish_service_callback
        self.service_callback = finish_callback
        self.start_reactor()
