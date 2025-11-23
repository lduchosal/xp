"""Service for downloading XP24 action tables via Conbus protocol."""

import logging
from typing import Any, Optional, Union

from psygnal import Signal

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
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class MsActionTableError(Exception):
    """Raised when XP24 action table operations fail."""

    pass


class MsActionTableDownloadService:
    """
    Service for downloading MS action tables via Conbus protocol.

    Uses ConbusEventProtocol to download action tables from XP20, XP24, or XP33 modules.
    Emits signals for progress updates, errors, and completion.

    Attributes:
        conbus_protocol: Protocol instance for Conbus communication.
        on_progress: Signal emitted for progress updates (str).
        on_error: Signal emitted for errors (str).
        on_finish: Signal emitted when XP download completes (Xp20MsActionTable, str).
    """

    on_progress: Signal = Signal(str)
    on_error: Signal = Signal(str)
    on_finish: Signal = Signal(object, list[str])

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        xp20ms_serializer: Xp20MsActionTableSerializer,
        xp24ms_serializer: Xp24MsActionTableSerializer,
        xp33ms_serializer: Xp33MsActionTableSerializer,
        telegram_service: TelegramService,
    ) -> None:
        """Initialize the MS action table service.

        Args:
            conbus_protocol: ConbusEventProtocol instance.
            xp20ms_serializer: XP20 MS action table serializer.
            xp24ms_serializer: XP24 MS action table serializer.
            xp33ms_serializer: XP33 MS action table serializer.
            telegram_service: Telegram service for parsing.
        """
        self.conbus_protocol = conbus_protocol
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
        self.msactiontable_data: list[str] = []
        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection made event."""
        self.logger.debug(
            "Connection established, sending download msactiontable telegram"
        )
        self.conbus_protocol.send_telegram(
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
            self.on_progress.emit(".")

            self.conbus_protocol.send_telegram(
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
            msactiontable_short = self.serializer.format_decoded_output(msactiontable)
            self.succeed(msactiontable, msactiontable_short)
            return

        self.logger.debug("Invalid msactiontable response")

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Timeout occurred")
        self.failed("Timeout")

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.on_error.emit(message)

    def succeed(
        self,
        msactiontable: Union[Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable],
        msactiontable_short: list[str],
    ) -> None:
        """Handle succeed connection event.

        Args:
            msactiontable: result.
            msactiontable_short: result in short form.
        """
        # Emit to the appropriate signal based on module type
        self.on_finish.emit(msactiontable, msactiontable_short)

    def start(
        self,
        serial_number: str,
        xpmoduletype: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Setup download parameters.

        Args:
            serial_number: Module serial number.
            xpmoduletype: XP module type (xp20, xp24, xp33).
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
            self.conbus_protocol.timeout_seconds = timeout_seconds

    def set_timeout(self, timeout_seconds: float) -> None:
        """Set operation timeout.

        Args:
            timeout_seconds: Timeout in seconds.
        """
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.start_reactor()

    def stop_reactor(self) -> None:
        """Stop the reactor."""
        self.conbus_protocol.stop_reactor()

    def __enter__(self) -> "MsActionTableDownloadService":
        """Enter context manager.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for singleton reuse
        self.msactiontable_data = []
        self.serial_number = ""
        self.xpmoduletype = ""
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        # Disconnect protocol signals
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        # Disconnect service signals
        self.on_progress.disconnect()
        self.on_error.disconnect()
        self.on_finish.disconnect()
        # Stop reactor
        self.stop_reactor()
