"""Conbus Auto Report Service for getting and setting module auto report status.

This service handles auto report status operations for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_autoreport import ConbusAutoreportResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol


class ConbusAutoreportSetService(ConbusProtocol):
    """
    Service for receiving telegrams from Conbus servers.

    Uses composition with ConbusService to provide receive-only functionality
    for collecting waiting event telegrams from the server.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus client send service"""
        super().__init__(cli_config, reactor)
        self.serial_number: str = ""
        self.status: bool = False
        self.finish_callback: Optional[Callable[[ConbusAutoreportResponse], None]] = (
            None
        )
        self.service_response: ConbusAutoreportResponse = ConbusAutoreportResponse(
            success=False,
            serial_number=self.serial_number,
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        # Convert boolean to appropriate value
        status_value = "PP" if self.status else "AA"
        status_text = "on" if self.status else "off"

        self.logger.debug("Connection established, set autoreport to %s", status_text)
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.WRITE_CONFIG,
            data_value=f"{DataPointType.AUTO_REPORT_STATUS.value}{status_value}",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        self.logger.debug("Autoreport reply telegram sent %s", telegram_sent)
        self.service_response.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:

        self.logger.debug(f"Telegram received: {telegram_received}")
        if not self.service_response.received_telegrams:
            self.service_response.received_telegrams = []
        self.service_response.received_telegrams.append(telegram_received.frame)

        if not (
            telegram_received.checksum_valid
            and telegram_received.telegram_type == TelegramType.REPLY
            and telegram_received.serial_number == self.serial_number
            and telegram_received.system_function
            in (SystemFunction.ACK, SystemFunction.NAK)
        ):
            self.logger.debug(f"Not a reply telegram received: {telegram_received}")
            return

        self.service_response.success = True
        self.service_response.timestamp = datetime.now()
        self.service_response.result = telegram_received.system_function.name
        self.service_response.auto_report_status = "on" if self.status else "off"

        self.logger.debug("Received autoreport reply telegram")
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def failed(self, message: str) -> None:
        self.logger.debug(f"Failed with message: {message}")
        self.service_response.success = False
        self.service_response.error = message
        self.service_response.timestamp = datetime.now()
        if self.finish_callback:
            self.finish_callback(self.service_response)

    def set_autoreport_status(
        self,
        serial_number: str,
        status: bool,
        finish_callback: Callable[[ConbusAutoreportResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Set the auto report status for a specific module.

        Args:
            serial_number: 10-digit module serial number
            status: True for ON, False for OFF
            finish_callback: callback function to call when the autoreport status is
            timeout_seconds: timeout in seconds

        Returns:
            ConbusAutoreportResponse with operation result

        Raises:
            ConbusAutoreportError: If parameters are invalid
        """
        self.logger.info("Starting set_autoreport_status")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.finish_callback = finish_callback
        self.serial_number = serial_number
        self.status = status
        self.start_reactor()
