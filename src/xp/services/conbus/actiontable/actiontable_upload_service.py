"""Service for uploading ActionTable via Conbus protocol."""

import logging
from typing import Any, Callable, Optional

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig
from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.protocol import ConbusProtocol
from xp.services.telegram.telegram_service import TelegramService


class ActionTableUploadService(ConbusProtocol):
    """TCP client service for uploading action tables to Conbus modules.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses for action table uploads.
    """

    def __init__(
        self,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
        actiontable_serializer: ActionTableSerializer,
        telegram_service: TelegramService,
        conson_config: ConsonModuleListConfig,
    ) -> None:
        """Initialize the action table upload service.

        Args:
            cli_config: Conbus client configuration.
            reactor: Twisted reactor instance.
            actiontable_serializer: Action table serializer.
            telegram_service: Telegram service for parsing.
            conson_config: Conson module list configuration.
        """
        super().__init__(cli_config, reactor)
        self.serializer = actiontable_serializer
        self.telegram_service = telegram_service
        self.conson_config = conson_config
        self.serial_number: str = ""
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        self.success_callback: Optional[Callable[[], None]] = None

        # Upload state
        self.upload_data_chunks: list[str] = []
        self.current_chunk_index: int = 0

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def connection_established(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, sending upload actiontable telegram")
        self.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number=self.serial_number,
            system_function=SystemFunction.UPLOAD_ACTIONTABLE,
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

        self._handle_upload_response(reply_telegram)

    def _handle_upload_response(self, reply_telegram: Any) -> None:
        """Handle telegram responses during upload.

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

                self.send_telegram(
                    telegram_type=TelegramType.SYSTEM,
                    serial_number=self.serial_number,
                    system_function=SystemFunction.ACTIONTABLE,
                    data_value=f"{prefix_hex}{chunk}",
                )
                self.current_chunk_index += 1
                if self.progress_callback:
                    self.progress_callback(".")
            else:
                # All chunks sent, send EOF
                self.logger.debug("All chunks sent, sending EOF")
                self.send_telegram(
                    telegram_type=TelegramType.SYSTEM,
                    serial_number=self.serial_number,
                    system_function=SystemFunction.EOF,
                    data_value="00",
                )
                if self.success_callback:
                    self.success_callback()
                self._stop_reactor()
        elif reply_telegram.system_function == SystemFunction.NAK:
            self.logger.debug("Received NAK during upload")
            self.failed("Upload failed: NAK received")
        else:
            self.logger.debug(f"Unexpected response during upload: {reply_telegram}")

    def failed(self, message: str) -> None:
        """Handle failed connection event.

        Args:
            message: Failure message.
        """
        self.logger.debug(f"Failed: {message}")
        if self.error_callback:
            self.error_callback(message)
        self._stop_reactor()

    def start(
        self,
        serial_number: str,
        progress_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
        success_callback: Callable[[], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """Upload action table to module.

        Uploads the action table configuration to the specified module.

        Args:
            serial_number: Module serial number.
            progress_callback: Callback for progress updates.
            error_callback: Callback for errors.
            success_callback: Callback when upload completes successfully.
            timeout_seconds: Optional timeout in seconds.
        """
        self.logger.info("Starting actiontable upload")
        self.serial_number = serial_number
        if timeout_seconds:
            self.timeout_seconds = timeout_seconds
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        self.success_callback = success_callback

        # Find module
        module = self.conson_config.find_module(serial_number)
        if not module:
            self.failed(f"Module {serial_number} not found in conson.yml")
            return

        # Parse action table strings to ActionTable object
        try:
            module_action_table = module.action_table or []
            action_table = self.serializer.parse_action_table(module_action_table)
        except ValueError as e:
            self.logger.error(f"Invalid action table format: {e}")
            self.failed(f"Invalid action table format: {e}")
            return

        # Encode action table to hex string
        encoded_data = self.serializer.to_encoded_string(action_table)

        # Chunk the data into 64 byte chunks
        chunk_size = 64
        self.upload_data_chunks = [
            encoded_data[i : i + chunk_size]
            for i in range(0, len(encoded_data), chunk_size)
        ]
        self.current_chunk_index = 0

        self.logger.debug(
            f"Upload data encoded: {len(encoded_data)} chars, "
            f"{len(self.upload_data_chunks)} chunks"
        )

        self.start_reactor()
