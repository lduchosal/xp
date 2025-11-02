"""Service for downloading ActionTable via Conbus protocol."""

import logging
from dataclasses import asdict
from typing import Any, Callable, Dict, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.actiontable.actiontable import ActionTable
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ActionTableService(ConbusProtocol):
    """TCP client service for downloading action tables from Conbus modules.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses for action table downloads.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
        actiontable_serializer: ActionTableSerializer,
        telegram_service: TelegramService,
    ) -> None:
        """Initialize the action table download service.

        Args:
            cli_config: Conbus client configuration.
            reactor: Twisted reactor instance.
            actiontable_serializer: Action table serializer.
            telegram_service: Telegram service for parsing.
        """
        super().__init__(cli_config, reactor)
        self.serializer = actiontable_serializer
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[
            Callable[[ActionTable, Dict[str, Any], list[str]], None]
        ] = None

        self.actiontable_data: list[str] = []
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            "Connection established, sending download actiontable telegram"
        )
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.DOWNLOAD_ACTIONTABLE,
            data_value="00",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.logger.debug(f"Telegram sent: {telegram_sent}")

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

        Args:
            telegram_received: The telegram received event.
        """
        self.logger.debug(f"Telegram received: {telegram_received}")
        if (
            not telegram_received.checksum_valid
            or telegram_received.telegram_type != TelegramType.REPLY.value
            or telegram_received.serial_number != self.serial_number
        ):
            self.logger.debug("Not a reply response")
            return

        reply_telegram = self.telegram_service.parse_reply_telegram(
            telegram_received.frame
        )
        if reply_telegram.system_function not in (
            SystemFunction.ACTIONTABLE,
            SystemFunction.EOF,
        ):
            self.logger.debug("Not a actiontable response")
            return

        if reply_telegram.system_function == SystemFunction.ACTIONTABLE:
            self.logger.debug("Saving actiontable response")
            data_part = reply_telegram.data_value[2:]
            self.actiontable_data.append(data_part)
            if self.progress_callback:
                self.progress_callback(".")

            self.send_telegram(
                telegram_type=TelegramType.SYSTEM,
                serial_number=self.serial_number,
                system_function=SystemFunction.ACK,
                data_value="00",
            )
            return

        if reply_telegram.system_function == SystemFunction.EOF:
            all_data = "".join(self.actiontable_data)
            # Deserialize from received data
            actiontable = self.serializer.from_encoded_string(all_data)
            actiontable_dict = asdict(actiontable)
            actiontable_short = self.serializer.format_decoded_output(actiontable)
            if self.finish_callback:
                self.finish_callback(actiontable, actiontable_dict, actiontable_short)

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        if self.error_callback:
            self.error_callback(message)

    def start(
        self,
        serial_number: str,
        progress_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
        finish_callback: Callable[[ActionTable, Dict[str, Any], list[str]], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            serial_number: Module serial number.
            progress_callback: Callback for progress updates.
            error_callback: Callback for errors.
            finish_callback: Callback when download completes.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting actiontable")
        self.serial_number = serial_number
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        self.finish_callback = finish_callback
        self.start_reactor()
