"""Service for downloading XP24 action tables via Conbus protocol."""

import logging
from typing import Callable, Optional, Union

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.models.actiontable.msactiontable_xp24 import Xp24MsActionTable
from xp.models.actiontable.msactiontable_xp33 import Xp33MsActionTable
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.actiontable.msactiontable_xp20_serializer import (
    Xp20MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp33_serializer import (
    Xp33MsActionTableSerializer,
)
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class MsActionTableError(Exception):
    """Raised when XP24 action table operations fail."""

    pass


class MsActionTableService(ConbusProtocol):
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
        xp20ms_serializer: Xp20MsActionTableSerializer,
        xp24ms_serializer: Xp24MsActionTableSerializer,
        xp33ms_serializer: Xp33MsActionTableSerializer,
        telegram_service: TelegramService,
    ) -> None:
        """Initialize the Conbus client send service.

        Args:
            cli_config: Conbus client configuration.
            reactor: Twisted reactor instance.
            xp20ms_serializer: XP20 MS action table serializer.
            xp24ms_serializer: XP24 MS action table serializer.
            xp33ms_serializer: XP33 MS action table serializer.
            telegram_service: Telegram service for parsing.
        """
        super().__init__(cli_config, reactor)
        self.xp20ms_serializer = xp20ms_serializer
        self.xp24ms_serializer = xp24ms_serializer
        self.xp33ms_serializer = xp33ms_serializer
        self.serializer: Union[
            Xp20MsActionTableSerializer,
            Xp24MsActionTableSerializer,
            Xp33MsActionTableSerializer,
        ] = xp20ms_serializer
        self.telegram_service = telegram_service
        self.serial_number: str = ""
        self.xpmoduletype: str = ""
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        self.finish_callback: Optional[
            Callable[
                [Union[Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable, None]],
                None,
            ]
        ] = None
        self.msactiontable_data: list[str] = []
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            "Connection established, sending download msactiontable telegram"
        )
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.DOWNLOAD_MSACTIONTABLE,
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
            SystemFunction.MSACTIONTABLE,
            SystemFunction.ACK,
            SystemFunction.NAK,
            SystemFunction.EOF,
        ):
            self.logger.debug("Not a msactiontable response")
            return

        if reply_telegram.system_function == SystemFunction.ACK:
            self.logger.debug("Received ACK")
            return

        if reply_telegram.system_function == SystemFunction.NAK:
            self.logger.debug("Received NAK")
            self.failed("Received NAK")
            return

        if reply_telegram.system_function == SystemFunction.MSACTIONTABLE:
            self.logger.debug("Received MSACTIONTABLE")
            self.msactiontable_data.extend(
                (reply_telegram.data, reply_telegram.data_value)
            )
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
            self.logger.debug("Received EOF")
            all_data = "".join(self.msactiontable_data)
            # Deserialize from received data
            msactiontable = self.serializer.from_data(all_data)
            self.succeed(msactiontable)
            return

        self.logger.debug("Invalid msactiontable response")

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        if self.error_callback:
            self.error_callback(message)
        self._stop_reactor()

    def succeed(
        self,
        msactiontable: Union[Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable],
    ) -> None:
        """Handle succeed connection event.

        Args:
            msactiontable: result.
        """
        if self.finish_callback:
            self.finish_callback(msactiontable)
        self._stop_reactor()

    def start(
        self,
        serial_number: str,
        xpmoduletype: str,
        progress_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
        finish_callback: Callable[
            [Union[Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable, None]], None
        ],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Run reactor in dedicated thread with its own event loop.

        Args:
            serial_number: Module serial number.
            xpmoduletype: XP module type (xp20, xp24, xp33).
            progress_callback: Callback for progress updates.
            error_callback: Callback for errors.
            finish_callback: Callback when download completes.
            timeout_seconds: Optional timeout in seconds.

        Raises:
            MsActionTableError: If unsupported module type is provided.
        """
        self.logger.info("Starting msactiontable")
        self.serial_number = serial_number
        self.xpmoduletype = xpmoduletype
        if xpmoduletype == "xp20":
            self.serializer = self.xp20ms_serializer
        elif xpmoduletype == "xp24":
            self.serializer = self.xp24ms_serializer
        elif xpmoduletype == "xp33":
            self.serializer = self.xp33ms_serializer
        else:
            raise MsActionTableError(f"Unsupported module type: {xpmoduletype}")

        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        self.finish_callback = finish_callback
        self.start_reactor()
