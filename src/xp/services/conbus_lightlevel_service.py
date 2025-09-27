"""Conbus Lightlevel Service for controlling light levels on Conbus modules.

This service implements lightlevel control operations for XP modules,
including setting specific light levels, turning lights on/off, and
querying current light levels.
"""

import logging
from datetime import datetime
from typing import Optional, Any

from .conbus_service import ConbusService
from .conbus_datapoint_service import ConbusDatapointService
from ..models.conbus_lightlevel import ConbusLightlevelResponse
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from ..services.telegram_service import TelegramService


class ConbusLightlevelError(Exception):
    """Raised when Conbus lightlevel operations fail"""

    pass


class ConbusLightlevelService:
    """
    Service for controlling light levels on Conbus modules.

    Manages lightlevel operations including setting specific levels,
    turning lights on/off, and querying current states.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus lightlevel service"""

        # Service dependencies
        self.telegram_service = TelegramService()
        self.conbus_service = ConbusService(config_path)
        self.datapoint_service = ConbusDatapointService(config_path)

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> "ConbusLightlevelService":
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        # Cleanup logic if needed
        pass

    def set_lightlevel(
        self, serial_number: str, output_number: int, level: int
    ) -> ConbusLightlevelResponse:
        """Set light level for a specific output on a module.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-based)
            level: Light level percentage (0-100)

        Returns:
            ConbusLightlevelResponse with operation result
        """

        # Validate output_number range (0-8)
        if not 0 <= output_number <= 8:
            return ConbusLightlevelResponse(
                success=False,
                serial_number=serial_number,
                output_number=output_number,
                level=level,
                timestamp=datetime.now(),
                error=f"Output number must be between 0 and 8, got {output_number}",
            )

        # Validate level range
        if not 0 <= level <= 100:
            return ConbusLightlevelResponse(
                success=False,
                serial_number=serial_number,
                output_number=output_number,
                level=level,
                timestamp=datetime.now(),
                error=f"Light level must be between 0 and 100, got {level}",
            )

        # Format data as output_number:level (e.g., "02:050")
        data = f"{output_number:02d}:{level:03d}"

        # Send telegram using WRITE_CONFIG function with MODULE_LIGHT_LEVEL datapoint
        response = self.conbus_service.send_telegram(
            serial_number,
            SystemFunction.WRITE_CONFIG,  # "04"
            f"{DataPointType.MODULE_LIGHT_LEVEL.value}{data}",  # "15" + "02:050"
        )

        return ConbusLightlevelResponse(
            success=response.success,
            serial_number=serial_number,
            output_number=output_number,
            level=level,
            timestamp=response.timestamp or datetime.now(),
            sent_telegram=response.sent_telegram,
            received_telegrams=response.received_telegrams,
            error=response.error,
        )

    def turn_off(
        self, serial_number: str, output_number: int
    ) -> ConbusLightlevelResponse:
        """Turn off light (set level to 0) for a specific output.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-8)

        Returns:
            ConbusLightlevelResponse with operation result
        """
        return self.set_lightlevel(serial_number, output_number, 0)

    def turn_on(
        self, serial_number: str, output_number: int
    ) -> ConbusLightlevelResponse:
        """Turn on light (set level to 80%) for a specific output.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-8)

        Returns:
            ConbusLightlevelResponse with operation result
        """
        return self.set_lightlevel(serial_number, output_number, 80)

    def get_lightlevel(
        self, serial_number: str, output_number: int
    ) -> ConbusLightlevelResponse:
        """Query current light level for a specific output.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-8)

        Returns:
            ConbusLightlevelResponse with current light level
        """

        # Query MODULE_LIGHT_LEVEL datapoint
        datapoint_response = self.datapoint_service.query_datapoint(
            DataPointType.MODULE_LIGHT_LEVEL, serial_number
        )

        if not datapoint_response.success:
            return ConbusLightlevelResponse(
                success=False,
                serial_number=serial_number,
                output_number=output_number,
                level=None,
                timestamp=datetime.now(),
                error=datapoint_response.error or "Failed to query light level",
            )

        # Parse the response to extract level for specific output
        level = None
        if (
            datapoint_response.datapoint_telegram
            and datapoint_response.datapoint_telegram.data_value
        ):
            try:
                # Parse response format like "00:050,01:025,02:100"
                data_value = str(datapoint_response.datapoint_telegram.data_value)
                for output_data in data_value.split(","):
                    if ":" in output_data:
                        output_str, level_str = output_data.split(":")
                        if int(output_str) == output_number:
                            level = int(level_str)
                            break
            except (ValueError, AttributeError) as e:
                self.logger.debug(f"Failed to parse light level data: {e}")

        return ConbusLightlevelResponse(
            success=datapoint_response.success,
            serial_number=serial_number,
            output_number=output_number,
            level=level,
            timestamp=datetime.now(),
            sent_telegram=datapoint_response.sent_telegram,
            received_telegrams=datapoint_response.received_telegrams,
            error=datapoint_response.error if level is None else None,
        )
