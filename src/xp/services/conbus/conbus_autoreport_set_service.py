"""Conbus Auto Report Service for getting and setting module auto report status.

This service handles auto report status operations for modules through Conbus telegrams.
"""

import logging
from typing import Callable, Optional

from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.write_config_service import WriteConfigService


class ConbusAutoreportSetService:
    """
    Service for setting auto report status on Conbus modules.

    Uses ConbusProtocol to provide auto report configuration functionality
    for enabling/disabling automatic reporting on modules.
    """

    def __init__(self, write_config_service: WriteConfigService) -> None:
        """Initialize the Conbus autoreport set service.

        Args:
            write_config_service: Write config service.
        """
        self.write_config_service: WriteConfigService = write_config_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def set_autoreport_status(
        self,
        serial_number: str,
        status: bool,
        finish_callback: Callable[[ConbusWriteConfigResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Set the auto report status for a specific module.

        Args:
            serial_number: 10-digit module serial number.
            status: True for ON, False for OFF.
            finish_callback: Callback function to call when operation completes.
            timeout_seconds: Timeout in seconds.
        """
        self.logger.info("Starting set_autoreport_status")

        # Convert boolean to appropriate value
        data_value = "PP" if status else "AA"

        self.write_config_service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=data_value,
            finish_callback=finish_callback,
            timeout_seconds=timeout_seconds,
        )
