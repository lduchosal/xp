"""Service for uploading ActionTable via Conbus protocol."""

import logging
from typing import Any, Optional

from psygnal import Signal

from xp.models.actiontable.actiontable_type import ActionTableType2
from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
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


class ActionTableUploadService:
    """
    TCP client service for uploading action tables and MS action tables to Conbus
    modules.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses for action table uploads.

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
        actiontable_serializer: ActionTableSerializer,
        xp20ms_serializer: Xp20MsActionTableSerializer,
        xp24ms_serializer: Xp24MsActionTableSerializer,
        xp33ms_serializer: Xp33MsActionTableSerializer,
        telegram_service: TelegramService,
        conson_config: ConsonModuleListConfig,
    ) -> None:
        """
        Initialize the action table upload service.

        Args:
            conbus_protocol: ConbusEventProtocol for communication.
            actiontable_serializer: Action table serializer.
            xp20ms_serializer: XP20 MS action table serializer.
            xp24ms_serializer: XP24 MS action table serializer.
            xp33ms_serializer: XP33 MS action table serializer.
            telegram_service: Telegram service for parsing.
            conson_config: Conson module list configuration.
        """
        self.conbus_protocol = conbus_protocol
        self.actiontable_serializer = actiontable_serializer
        self.xp20ms_serializer = xp20ms_serializer
        self.xp24ms_serializer = xp24ms_serializer
        self.xp33ms_serializer = xp33ms_serializer
        self.telegram_service = telegram_service
        self.conson_config = conson_config
        self.serial_number: str = ""
        self.xpmoduletype: str = ""
        self.actiontable_type: ActionTableType2 = ActionTableType2.ACTIONTABLE

        # Upload state
        self.upload_data_chunks: list[str] = []
        self.current_chunk_index: int = 0
        self._eof_sent: bool = False

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
        self.logger.debug("Connection established, sending upload actiontable telegram")

        system_function = (
            SystemFunction.UPLOAD_ACTIONTABLE
            if self.actiontable_type == ActionTableType2.ACTIONTABLE
            else SystemFunction.UPLOAD_MSACTIONTABLE
        )

        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=system_function,
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
            # Send next chunk or EOF
            if self.current_chunk_index < len(self.upload_data_chunks):
                chunk = self.upload_data_chunks[self.current_chunk_index]
                self.logger.debug(f"Sending chunk {self.current_chunk_index + 1}")

                # Calculate prefix: AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ, AK, AL, AM, AN, AO
                # First character: 'A' (fixed)
                # Second character: 'A' + chunk_index (sequential counter A-O for 15 chunks)
                prefix_hex = f"AAA{ord('A') + self.current_chunk_index:c}"

                system_function = (
                    SystemFunction.ACTIONTABLE
                    if self.actiontable_type == ActionTableType2.ACTIONTABLE
                    else SystemFunction.MSACTIONTABLE
                )

                self.conbus_protocol.send_telegram(
                    telegram_type=TelegramType.SYSTEM,
                    serial_number=self.serial_number,
                    system_function=system_function,
                    data_value=f"{prefix_hex}{chunk}",
                )
                self.current_chunk_index += 1
                self.on_progress.emit(".")
            elif not self._eof_sent:
                # All chunks sent, send EOF
                self.logger.debug("All chunks sent, sending EOF")
                self.conbus_protocol.send_telegram(
                    telegram_type=TelegramType.SYSTEM,
                    serial_number=self.serial_number,
                    system_function=SystemFunction.EOF,
                    data_value="00",
                )
                self.on_progress.emit("END")
                self.logger.debug("EOF sent, waiting for last ACK")
                self._eof_sent = True
            else:
                self.logger.debug("Last ACK received, closing connection")
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
        actiontable_type: ActionTableType2,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Upload action table or MS action table to module.

        Uploads the action table configuration to the specified module.
        Module type will decide which actiontable to use.

        Args:
            serial_number: Module serial number.
            actiontable_type: True if actionTable false for MS action table.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting actiontable upload")
        self.serial_number = serial_number
        self.actiontable_type = actiontable_type

        if timeout_seconds:
            self.conbus_protocol.timeout_seconds = timeout_seconds

        # Find module
        module = self.conson_config.find_module(serial_number)
        if not module:
            self.failed(f"Module {serial_number} not found in conson.yml")
            return

        # Parse action table strings to ActionTable object
        try:
            encoded_data = self.get_encoded_action_table(module)
            # Chunk the data into 64 byte chunks
            chunk_size = 64
            self.upload_data_chunks = [
                encoded_data[i : i + chunk_size]
                for i in range(0, len(encoded_data), chunk_size)
            ]
            self.current_chunk_index = 0

        except ValueError as e:
            self.logger.error(f"Invalid action table format: {e}")
            self.failed(f"Invalid action table format: {e}")
            return

        self.logger.debug(
            f"Upload data encoded: {len(encoded_data)} chars, "
            f"{len(self.upload_data_chunks)} chunks"
        )

    def get_encoded_action_table(self, module: ConsonModuleConfig) -> str:
        """
        Get encoded action table string for upload.

        Args:
            module: Module configuration containing action table data.

        Returns:
            Hex-encoded action table string ready for transmission.
        """
        msactiontable = (
            True if self.actiontable_type == ActionTableType2.MSACTIONTABLE else False
        )
        # Parse MS action table from short format (first element)
        if msactiontable and module.module_type.lower() == "xp20":
            xp20_short_table = module.xp20_msaction_table or []
            xp20_actiontable = self.xp20ms_serializer.from_short_string(
                xp20_short_table
            )
            encoded_string = self.xp20ms_serializer.to_encoded_string(xp20_actiontable)
        elif msactiontable and module.module_type.lower() == "xp24":
            xp24_short_table = module.xp24_msaction_table or []
            xp24_actiontable = self.xp24ms_serializer.from_short_string(
                xp24_short_table
            )
            encoded_string = self.xp24ms_serializer.to_encoded_string(xp24_actiontable)
        elif msactiontable and module.module_type.lower() == "xp33":
            xp33_short_table = module.xp33_msaction_table or []
            xp33_actiontable = self.xp33ms_serializer.from_short_string(
                xp33_short_table
            )
            encoded_string = self.xp33ms_serializer.to_encoded_string(xp33_actiontable)
        else:
            short_table = module.action_table or []
            actiontable = self.actiontable_serializer.from_short_string(short_table)
            encoded_string = self.actiontable_serializer.to_encoded_string(actiontable)

        # Serialize to telegram data (64 characters: AAAA + 64 data chars)
        return encoded_string

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

    def __enter__(self) -> "ActionTableUploadService":
        """Enter context manager - reset state for singleton reuse.

        Returns:
            Self for context manager protocol.
        """
        # Reset state
        self.upload_data_chunks = []
        self.current_chunk_index = 0
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
