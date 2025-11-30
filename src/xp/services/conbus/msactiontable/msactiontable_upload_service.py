"""Service for uploading MS action tables via Conbus protocol."""

import logging
from typing import Any, Optional, Union

from psygnal import Signal

from xp.models.config.conson_module_config import ConsonModuleListConfig
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


class MsActionTableUploadError(Exception):
    """Raised when MS action table upload operations fail."""

    pass


class MsActionTableUploadService:
    """
    TCP client service for uploading MS action tables to Conbus modules.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses for MS action table uploads.

    Attributes:
        on_progress: Signal emitted with telegram frame when progress is made.
        on_error: Signal emitted with error message string when an error occurs.
        on_finish: Signal emitted with bool (True on success) when upload completes.
    """

    on_progress: Signal = Signal(str)
    on_error: Signal = Signal(str)
    on_finish: Signal = Signal(bool)  # True on success

    def __init__(
        self,
        conbus_protocol: ConbusEventProtocol,
        xp20ms_serializer: Xp20MsActionTableSerializer,
        xp24ms_serializer: Xp24MsActionTableSerializer,
        xp33ms_serializer: Xp33MsActionTableSerializer,
        telegram_service: TelegramService,
        conson_config: ConsonModuleListConfig,
    ) -> None:
        """
        Initialize the MS action table upload service.

        Args:
            conbus_protocol: ConbusEventProtocol for communication.
            xp20ms_serializer: XP20 MS action table serializer.
            xp24ms_serializer: XP24 MS action table serializer.
            xp33ms_serializer: XP33 MS action table serializer.
            telegram_service: Telegram service for parsing.
            conson_config: Conson module list configuration.
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
        self.conson_config = conson_config
        self.serial_number: str = ""
        self.xpmoduletype: str = ""

        # Upload state
        self.upload_data: str = ""
        self.upload_initiated: bool = False

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug(
            "Connection established, sending upload msactiontable telegram"
        )
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.UPLOAD_MSACTIONTABLE,
            data_value="00",
        )

    def telegram_sent(self, telegram_sent: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram_sent: The telegram that was sent.
        """
        self.logger.debug(f"Telegram sent: {telegram_sent}")

    def telegram_received(self, telegram_received: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

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

        self._handle_upload_response(reply_telegram)

    def _handle_upload_response(self, reply_telegram: Any) -> None:
        """
        Handle telegram responses during upload.

        Args:
            reply_telegram: Parsed reply telegram.
        """
        if reply_telegram.system_function == SystemFunction.ACK:
            self.logger.debug("Received ACK for upload")

            if not self.upload_initiated:
                # First ACK - send data chunk
                self.logger.debug("Sending msactiontable data")
                self.conbus_protocol.send_telegram(
                    telegram_type=TelegramType.SYSTEM,
                    serial_number=self.serial_number,
                    system_function=SystemFunction.MSACTIONTABLE,
                    data_value=self.upload_data,
                )
                self.upload_initiated = True
                self.on_progress.emit(".")
            else:
                # Second ACK - send EOF
                self.logger.debug("Data sent, sending EOF")
                self.conbus_protocol.send_telegram(
                    telegram_type=TelegramType.SYSTEM,
                    serial_number=self.serial_number,
                    system_function=SystemFunction.EOF,
                    data_value="00",
                )
                self.on_finish.emit(True)
        elif reply_telegram.system_function == SystemFunction.NAK:
            self.logger.debug("Received NAK during upload")
            self.failed("Upload failed: NAK received")
        else:
            self.logger.debug(f"Unexpected response during upload: {reply_telegram}")

    def timeout(self) -> None:
        """Handle timeout event."""
        self.logger.debug("Upload timeout")
        self.failed("Upload timeout")

    def failed(self, message: str) -> None:
        """
        Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        self.on_error.emit(message)

    def start(
        self,
        serial_number: str,
        xpmoduletype: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Upload MS action table to module.

        Uploads the MS action table configuration to the specified module.

        Args:
            serial_number: Module serial number.
            xpmoduletype: XP module type (xp20, xp24, xp33).
            timeout_seconds: Optional timeout in seconds.

        Raises:
            MsActionTableUploadError: If configuration or validation errors occur.
        """
        self.logger.info("Starting msactiontable upload")
        self.serial_number = serial_number
        self.xpmoduletype = xpmoduletype

        # Select serializer based on module type
        if xpmoduletype == "xp20":
            self.serializer = self.xp20ms_serializer
            config_field = "xp20_msaction_table"
        elif xpmoduletype == "xp24":
            self.serializer = self.xp24ms_serializer
            config_field = "xp24_msaction_table"
        elif xpmoduletype == "xp33":
            self.serializer = self.xp33ms_serializer
            config_field = "xp33_msaction_table"
        else:
            raise MsActionTableUploadError(f"Unsupported module type: {xpmoduletype}")

        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds

        # Find module
        module = self.conson_config.find_module(serial_number)
        if not module:
            self.failed(f"Module {serial_number} not found in conson.yml")
            return

        # Validate module type matches
        if module.module_type.lower() != xpmoduletype.lower():
            self.failed(
                f"Module type mismatch: module has type {module.module_type}, "
                f"but {xpmoduletype} was specified"
            )
            return

        # Get msactiontable config for the module type
        msactiontable_config = getattr(module, config_field, None)

        if not msactiontable_config:
            self.failed(
                f"Module {serial_number} does not have {config_field} configured in conson.yml"
            )
            return

        if not isinstance(msactiontable_config, list) or len(msactiontable_config) == 0:
            self.failed(
                f"Module {serial_number} has empty {config_field} list in conson.yml"
            )
            return

        # Parse MS action table from short format (first element)
        try:
            short_format = msactiontable_config
            msactiontable: Union[
                "Xp20MsActionTable", "Xp24MsActionTable", "Xp33MsActionTable"
            ]
            if xpmoduletype == "xp20":
                from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable

                msactiontable = Xp20MsActionTable.from_short_format(short_format)
            elif xpmoduletype == "xp24":
                from xp.models.actiontable.msactiontable_xp24 import Xp24MsActionTable

                msactiontable = Xp24MsActionTable.from_short_format(short_format)
            elif xpmoduletype == "xp33":
                from xp.models.actiontable.msactiontable_xp33 import Xp33MsActionTable

                msactiontable = Xp33MsActionTable.from_short_format(short_format)
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Invalid msactiontable format: {e}")
            self.failed(f"Invalid msactiontable format: {e}")
            return

        # Serialize to telegram data (64 characters: AAAA + 64 data chars)
        self.upload_data = "AAAA" + self.serializer.to_encoded_string(msactiontable)  # type: ignore[arg-type]

        self.logger.debug(
            f"Upload data encoded: {len(self.upload_data)} chars (single chunk)"
        )

    def set_timeout(self, timeout_seconds: float) -> None:
        """
        Set operation timeout.

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

    def __enter__(self) -> "MsActionTableUploadService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state
        self.upload_data = ""
        self.upload_initiated = False
        self.serial_number = ""
        self.xpmoduletype = ""
        return self

    def __exit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        """Exit context manager - cleanup signals and reactor."""
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
