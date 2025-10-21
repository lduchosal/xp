"""Conbus Link Number Service for setting module link numbers.

This service handles setting link numbers for modules through Conbus telegrams.
"""

import logging
from typing import Callable, Optional

from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.write_config_service import WriteConfigService


class ConbusLinknumberSetService:
    """
    Service for setting module link numbers via Conbus telegrams.

    Handles link number assignment by sending F04D04 telegrams and processing
    ACK/NAK responses from modules.
    """

    def __init__(self, write_config_service: WriteConfigService) -> None:
        """Initialize the Conbus link number set service.

        Args:
            write_config_service: Service for writing config.
        """
        self.write_config_service: WriteConfigService = write_config_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def set_linknumber(
        self,
        serial_number: str,
        link_number: int,
        finish_callback: Callable[[ConbusWriteConfigResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Set the link number for a specific module.

        Args:
            serial_number: 10-digit module serial number.
            link_number: Link number to set (0-99).
            finish_callback: Callback function to call when operation completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting set_linknumber")

        # Validate parameters before sending
        data_value = f"{link_number: 02d}"
        self.write_config_service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=data_value,
            finish_callback=finish_callback,
            timeout_seconds=timeout_seconds,
        )
