"""Conbus Auto Report Service for getting and setting module auto report status.

This service handles auto report status operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig, ConbusDatapointResponse
from xp.models.conbus.conbus_lightlevel import ConbusLightlevelResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.telegram.telegram_service import TelegramService


class ConbusLightlevelGetService(ConbusDatapointService):
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
        self.output_number: int = 0
        self.service_callback: Optional[Callable[[ConbusLightlevelResponse], None]] = (
            None
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def finish_service_callback(
        self, datapoint_response: ConbusDatapointResponse
    ) -> None:

        self.logger.debug("Parsing datapoint response")

        level = 0
        if datapoint_response.success and datapoint_response.datapoint_telegram:
            for output_data in datapoint_response.datapoint_telegram.data_value.split(
                ","
            ):
                if ":" in output_data:
                    output_str, level_str = output_data.split(":")
                    if int(output_str) == self.output_number:
                        level_str = level_str.replace("[%]", "")
                        level = int(level_str)
                        break

        service_response = ConbusLightlevelResponse(
            success=datapoint_response.success,
            serial_number=self.serial_number,
            output_number=self.output_number,
            level=level,
            error=datapoint_response.error,
            sent_telegram=datapoint_response.sent_telegram,
            received_telegrams=datapoint_response.received_telegrams,
            timestamp=datetime.now(),
        )

        if self.service_callback:
            self.service_callback(service_response)

    def get_light_level(
        self,
        serial_number: str,
        output_number: int,
        finish_callback: Callable[[ConbusLightlevelResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Get the current auto report status for a specific module.

        Args:
            :param  serial_number: 10-digit module serial number
            :param  output_number: output module number
            :param  finish_callback: callback function to call when the lightlevel status is
            :param  timeout_seconds: timeout in seconds

        """
        self.logger.info("Starting get_lightlevel_status")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.output_number = output_number
        self.datapoint_type = DataPointType.MODULE_LIGHT_LEVEL

        self.finish_callback = self.finish_service_callback
        self.service_callback = finish_callback
        self.start_reactor()
