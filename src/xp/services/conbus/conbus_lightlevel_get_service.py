"""Conbus Auto Report Service for getting and setting module auto report status.

This service handles auto report status operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_lightlevel import ConbusLightlevelResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusLightlevelGetService(ConbusProtocol):
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
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.output_number: int = 0
        self.finish_callback: Optional[Callable[[ConbusLightlevelResponse], None]] = (
            None
        )
        self.service_response: ConbusLightlevelResponse = ConbusLightlevelResponse(
            success=False,
            serial_number=self.serial_number,
            output_number=self.output_number,
            level=0,
            timestamp=datetime.now(),
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        self.logger.debug("Connection established, retrieving lightlevel status...")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.READ_DATAPOINT,
            data_value=str(DataPointType.MODULE_LIGHT_LEVEL.value),
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
            self.logger.debug("Not a reply")
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )

        if (
            not reply_telegram
            or reply_telegram.system_function != SystemFunction.READ_DATAPOINT
            or reply_telegram.datapoint_type != DataPointType.MODULE_LIGHT_LEVEL
        ):
            self.logger.debug("Not a lightlevel telegram")
            return

        self.logger.debug("Received lightlevel status telegram")
        lightlevel = self.extract_lightlevel(reply_telegram)
        self.succeed(lightlevel)

    def extract_lightlevel(self, reply_telegram: ReplyTelegram) -> int:
        level = 0
        for output_data in reply_telegram.data_value.split(","):
            if ":" in output_data:
                output_str, level_str = output_data.split(":")
                if int(output_str) == self.output_number:
                    level_str = level_str.replace("[%]", "")
                    level = int(level_str)
                    break
        return level

    def succeed(self, lightlevel: int) -> None:
        self.service_response.success = True
        self.service_response.timestamp = datetime.now()
        self.service_response.serial_number = self.serial_number
        self.service_response.level = lightlevel
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def failed(self, message: str) -> None:
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.timestamp = datetime.now()
        self.service_response.error = message
        if self.finish_callback:
            self.finish_callback(self.service_response)

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
        self.finish_callback = finish_callback
        self.serial_number = serial_number
        self.output_number = output_number
        self.start_reactor()
