"""Conbus Lightlevel Service for controlling light levels on Conbus modules.

This service implements lightlevel control operations for XP modules,
including setting specific light levels, turning lights on/off, and
querying current light levels.
"""

import logging
from typing import Callable, Optional

from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.write_config_service import WriteConfigService


class ConbusLightlevelSetService:
    """
    Service for setting light level status on Conbus modules.

    Uses ConbusProtocol to provide light level configuration functionality
    for enabling/disabling automatic reporting on modules.
    """

    def __init__(self, write_config_service: WriteConfigService) -> None:
        """Initialize the Conbus lightlevel set service.

        Args:
            write_config_service: Write Config service.
        """
        self.write_config_service: WriteConfigService = write_config_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def set_lightlevel(
        self,
        serial_number: str,
        output_number: int,
        level: int,
        finish_callback: Callable[[ConbusWriteConfigResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Set light level for a specific output on a module.

        Args:
            serial_number: Module serial number.
            output_number: Output number (0-based, 0-8).
            level: Light level percentage (0-100).
            finish_callback: Callback function to call when operation completes.
            timeout_seconds: Optional timeout in seconds.

        Examples:
            xp conbus lightlevel set 0012345008 2 50
            xp conbus lightlevel set 0012345008 0 100
        """
        self.logger.info(
            f"Setting light level for {serial_number} output {output_number} to {level}%"
        )
        # Format data as output_number:level (e.g., "02:050")
        data_value = f"{output_number:02d}:{level:03d}"

        self.write_config_service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=data_value,
            finish_callback=finish_callback,
            timeout_seconds=timeout_seconds,
        )

    def turn_off(
        self,
        serial_number: str,
        output_number: int,
        finish_callback: Callable[[ConbusWriteConfigResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Turn off light (set level to 0) for a specific output.

        Args:
            serial_number: Module serial number.
            output_number: Output number (0-8).
            finish_callback: Callback function to call when operation completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.set_lightlevel(
            serial_number, output_number, 0, finish_callback, timeout_seconds
        )

    def turn_on(
        self,
        serial_number: str,
        output_number: int,
        finish_callback: Callable[[ConbusWriteConfigResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Turn on light (set level to 80%) for a specific output.

        Args:
            serial_number: Module serial number.
            output_number: Output number (0-8).
            finish_callback: Callback function to call when operation completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.set_lightlevel(
            serial_number, output_number, 80, finish_callback, timeout_seconds
        )
