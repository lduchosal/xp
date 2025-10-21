"""Conbus Lightlevel Get Service for getting module light levels.

This service handles light level query operations for modules through Conbus telegrams.
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
    Service for getting light levels from Conbus modules.

    Uses ConbusProtocol to provide light level query functionality
    for reading the current light level configuration from module outputs.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus lightlevel get service.

        Args:
            telegram_service: Service for parsing telegrams.
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event loop.
        """
        super().__init__(telegram_service, cli_config, reactor)
        self.output_number: int = 0
        self.finish_callback: Optional[Callable[[ConbusLightlevelResponse], None]] = (
            None
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def datapoint_finished_callback(
        self, datapoint_response: ConbusDatapointResponse
    ) -> None:
        """Process datapoint response and extract light level.

        Args:
            datapoint_response: The datapoint response from the module.
        """
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

        if self.finish_callback:
            self.finish_callback(service_response)

    def get_light_level(
        self,
        serial_number: str,
        output_number: int,
        finish_callback: Callable[[ConbusLightlevelResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Get the current light level for a specific module output.

        Args:
            serial_number: 10-digit module serial number.
            output_number: Output module number.
            finish_callback: Callback function to call when the light level is received.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting get_light_level")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.output_number = output_number
        self.datapoint_type = DataPointType.MODULE_LIGHT_LEVEL

        self.datapoint_finished_callback = self.datapoint_finished_callback
        self.finish_callback = finish_callback
        self.start_reactor()
