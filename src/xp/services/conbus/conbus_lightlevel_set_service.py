"""Conbus Lightlevel Service for controlling light levels on Conbus modules.

This service implements lightlevel control operations for XP modules,
including setting specific light levels, turning lights on/off, and
querying current light levels.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_lightlevel import ConbusLightlevelResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol


class ConbusLightlevelError(Exception):
    """Raised when Conbus lightlevel operations fail"""

    pass


class ConbusLightlevelSetService(ConbusProtocol):
    """
    Service for controlling light levels on Conbus modules.

    Manages lightlevel operations including setting specific levels,
    turning lights on/off, and querying current states.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ):
        """Initialize the Conbus lightlevel service"""
        super().__init__(cli_config, reactor)
        self.serial_number: str = ""
        self.output_number: int = 0
        self.level: int = 0
        self.finish_callback: Optional[Callable[[ConbusLightlevelResponse], None]] = (
            None
        )
        self.service_response: ConbusLightlevelResponse = ConbusLightlevelResponse(
            success=False,
            serial_number=self.serial_number,
            output_number=self.output_number,
            level=None,
            timestamp=datetime.now(),
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        self.logger.debug(
            f"Connection established, setting light level for output {self.output_number} to {self.level}%..."
        )

        # Format data as output_number:level (e.g., ""15" + "02:050")
        data_value = f"{DataPointType.MODULE_LIGHT_LEVEL.value}{self.output_number:02d}:{self.level:03d}"

        # Send telegram using WRITE_CONFIG function with MODULE_LIGHT_LEVEL datapoint
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.WRITE_CONFIG,  # "04"
            data_value=data_value,
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        self.service_response.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.service_response.received_telegrams:
            self.service_response.received_telegrams = []
        self.service_response.received_telegrams.append(telegram_received.frame)

        if (
            not telegram_received.checksum_valid
            or telegram_received.telegram_type != TelegramType.REPLY
            or telegram_received.serial_number != self.serial_number
        ):
            self.logger.debug("Not a reply for our serial number")
            return

        # Any valid reply means success (ACK or NAK)
        if telegram_received.telegram_type == TelegramType.REPLY:
            self.logger.debug("Received lightlevel response")
            self.succeed()

    def succeed(self) -> None:
        self.logger.debug("Succeed")
        self.service_response.success = True
        self.service_response.serial_number = self.serial_number
        self.service_response.output_number = self.output_number
        self.service_response.level = self.level
        self.service_response.timestamp = datetime.now()

        if self.finish_callback:
            self.finish_callback(self.service_response)

    def failed(self, message: str) -> None:
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.serial_number = self.serial_number
        self.service_response.output_number = self.output_number
        self.service_response.level = self.level
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message

        if self.finish_callback:
            self.finish_callback(self.service_response)

    def set_lightlevel(
        self,
        serial_number: str,
        output_number: int,
        level: int,
        finish_callback: Callable[[ConbusLightlevelResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Set light level for a specific output on a module.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-based, 0-8)
            level: Light level percentage (0-100)
            finish_callback: Callback function to call when operation completes
            timeout_seconds: Optional timeout in seconds

        Examples:
            \b
                xp conbus lightlevel set 0012345008 2 50
                xp conbus lightlevel set 0012345008 0 100
        """

        self.logger.info(
            f"Setting light level for {serial_number} output {output_number} to {level}%"
        )
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.finish_callback = finish_callback
        self.serial_number = serial_number
        self.output_number = output_number
        self.level = level

        # Validate output_number range (0-8)
        if not 0 <= self.output_number <= 8:
            self.failed(
                f"Output number must be between 0 and 8, got {self.output_number}"
            )
            return

        # Validate level range
        if not 0 <= self.level <= 100:
            self.failed(f"Light level must be between 0 and 100, got {self.level}")
            return

        self.start_reactor()

    def turn_off(
        self,
        serial_number: str,
        output_number: int,
        finish_callback: Callable[[ConbusLightlevelResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Turn off light (set level to 0) for a specific output.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-8)
            finish_callback: Callback function to call when operation completes
            timeout_seconds: Optional timeout in seconds
        """
        self.set_lightlevel(
            serial_number, output_number, 0, finish_callback, timeout_seconds
        )

    def turn_on(
        self,
        serial_number: str,
        output_number: int,
        finish_callback: Callable[[ConbusLightlevelResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Turn on light (set level to 80%) for a specific output.

        Args:
            serial_number: Module serial number
            output_number: Output number (0-8)
            finish_callback: Callback function to call when operation completes
            timeout_seconds: Optional timeout in seconds
        """
        self.set_lightlevel(
            serial_number, output_number, 80, finish_callback, timeout_seconds
        )
