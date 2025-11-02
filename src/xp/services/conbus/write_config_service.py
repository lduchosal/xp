"""Conbus Link Number Service for setting module link numbers.

This service handles setting link numbers for modules through Conbus telegrams.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class WriteConfigService(ConbusProtocol):
    """
    Service for writing module settings via Conbus telegrams.

    Handles setting assignment by sending F04DXX telegrams and processing
    ACK/NAK responses from modules.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ) -> None:
        """Initialize the Conbus link number set service.

        Args:
            telegram_service: Service for parsing telegrams.
            cli_config: Configuration for Conbus client connection.
            reactor: Twisted reactor for event loop.
        """
        super().__init__(cli_config, reactor)
        self.telegram_service = telegram_service
        self.datapoint_type: Optional[DataPointType] = None
        self.serial_number: str = ""
        self.data_value: str = ""
        self.write_config_finished_callback: Optional[
            Callable[[ConbusWriteConfigResponse], None]
        ] = None
        self.write_config_response: ConbusWriteConfigResponse = (
            ConbusWriteConfigResponse(
                success=False,
                serial_number=self.serial_number,
            )
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug(f"Connection established, writing config {self.data_value}.")

        # Validate parameters before sending
        if not self.serial_number or len(self.serial_number) != 10:
            self.failed(f"Serial number must be 10 digits, got: {self.serial_number}")
            return

        if len(self.data_value) < 2:
            self.failed(f"data_value must be at least 2 bytes, got: {self.data_value}")
            return

        if not self.datapoint_type:
            self.failed(f"datapoint_type must be defined, got: {self.datapoint_type}")
            return

        # Send WRITE_CONFIG telegram
        # Function F04 = WRITE_CONFIG,
        # Datapoint = D datapoint_type
        # Data = XX
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.WRITE_CONFIG,
            data_value=f"{self.datapoint_type.value}{self.data_value}",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.write_config_response.sent_telegram = telegram_sent

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")

        if not self.write_config_response.received_telegrams:
            self.write_config_response.received_telegrams = []
        self.write_config_response.received_telegrams.append(telegram_received.frame)

        if (
            not telegram_received.checksum_valid
            or telegram_received.telegram_type != TelegramType.REPLY
            or telegram_received.serial_number != self.serial_number
        ):
            self.logger.debug("Not a reply for our serial number")
            return

        # Parse the reply telegram
        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )

        if not reply_telegram or reply_telegram.system_function not in (
            SystemFunction.ACK,
            SystemFunction.NAK,
        ):
            self.logger.debug("Not a write config reply")
            return

        succeed = (
            True if reply_telegram.system_function == SystemFunction.ACK else False
        )
        self.finished(
            succeed_or_failed=succeed, system_function=reply_telegram.system_function
        )

    def failed(self, message: str) -> None:
        """Handle telegram failed event.

        Args:
            message: The error message.
        """
        self.logger.debug("Failed to send telegram")
        self.finished(succeed_or_failed=False, message=message)

    def finished(
        self,
        succeed_or_failed: bool,
        message: Optional[str] = None,
        system_function: Optional[SystemFunction] = None,
    ) -> None:
        """Handle successful link number set operation.

        Args:
            succeed_or_failed: succeed true, failed false.
            message: error message if any.
            system_function: The system function from the reply telegram.
        """
        self.logger.debug("finished writing config")
        self.write_config_response.success = succeed_or_failed
        self.write_config_response.error = message
        self.write_config_response.timestamp = datetime.now()
        self.write_config_response.serial_number = self.serial_number
        self.write_config_response.system_function = system_function
        self.write_config_response.datapoint_type = self.datapoint_type
        self.write_config_response.data_value = self.data_value
        if self.write_config_finished_callback:
            self.write_config_finished_callback(self.write_config_response)
        self._stop_reactor()

    def write_config(
        self,
        serial_number: str,
        datapoint_type: DataPointType,
        data_value: str,
        finish_callback: Callable[[ConbusWriteConfigResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Write config to a specific module.

        Args:
            serial_number: 10-digit module serial number.
            datapoint_type: the datapoint type to write to.
            data_value: the data to write.
            finish_callback: Callback function to call when operation completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting write_config")
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.serial_number = serial_number
        self.datapoint_type = datapoint_type
        self.data_value = data_value
        self.write_config_finished_callback = finish_callback
        self.start_reactor()
