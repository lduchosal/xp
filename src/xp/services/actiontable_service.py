"""Service for downloading ActionTable via Conbus protocol."""

import logging
from contextlib import suppress
from typing import Optional, Any

from . import TelegramService, TelegramParsingError
from .conbus_service import ConbusService, ConbusError
from .actiontable_serializer import ActionTableSerializer
from ..models.system_function import SystemFunction
from ..models.actiontable import ActionTable


class ActionTableError(Exception):
    """Raised when ActionTable operations fail"""

    pass


class ActionTableService:
    """Service for downloading ActionTable via Conbus"""

    def __init__(self, config_path: str = "cli.yml"):
        self.conbus_service = ConbusService(config_path)
        self.serializer = ActionTableSerializer()
        self.telegram_service = TelegramService()
        self.logger = logging.getLogger(__name__)

    def download_actiontable(self, serial_number: str) -> ActionTable:
        """Download action table from XP module"""
        try:
            ack_received = False
            actiontable_received = False
            eof_received = False
            actiontable_data: list[bytes] = []

            def on_data_received(telegrams: list[str]) -> None:
                nonlocal ack_received, actiontable_received, actiontable_data, eof_received

                self.logger.debug(f"Data received telegrams: {telegrams}")

                if self._is_ack(telegrams):
                    self.logger.debug("Received ack")
                    ack_received = True

                if self._is_eof(telegrams):
                    self.logger.debug("Received eof")
                    eof_received = True

                table_data = self._get_actiontable_data(telegrams)
                if table_data is not None:
                    actiontable_received = True
                    actiontable_data.append(table_data)
                    self.logger.debug("Received actiontable data")

                if ack_received and actiontable_received:
                    ack_received = False
                    actiontable_received = False
                    # Send continue signal to get next chunk
                    self.conbus_service.send_telegram(
                        serial_number,
                        SystemFunction.ACK,  # F18
                        "00",  # Continue signal
                        on_data_received,
                    )
                    return

                if not eof_received:
                    self.conbus_service.receive_responses(0.01, on_data_received)

            # Send F11D query to request ActionTable
            self.conbus_service.send_telegram(
                serial_number,
                SystemFunction.DOWNLOAD_ACTIONTABLE,  # F11D
                "00",  # ActionTable query
                on_data_received,
            )

            # Combine all received data chunks
            self.logger.debug(
                f"Received actiontable_data chunks: {len(actiontable_data)}"
            )
            if not actiontable_data:
                raise ActionTableError("No actiontable data received")

            # Concatenate all data chunks
            combined_data = b"".join(actiontable_data)
            self.logger.debug(f"Combined data length: {len(combined_data)}")

            # Deserialize from received data
            return self.serializer.from_data(combined_data)

        except ConbusError as e:
            raise ActionTableError(f"Conbus communication failed: {e}") from e
        except Exception as e:
            raise ActionTableError(f"Conbus communication failed: {e}") from e

    def format_decoded_output(self, actiontable: ActionTable) -> str:
        """Format action table as decoded output"""
        return self.serializer.format_decoded_output(actiontable)

    def format_encoded_output(self, actiontable: ActionTable) -> str:
        """Format action table as encoded output"""
        return self.serializer.to_encoded_string(actiontable)

    def _is_ack(self, received_telegrams: list[str]) -> bool:
        """Check if any telegram is an ACK response"""
        for response in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(response)
                if reply_telegram.system_function == SystemFunction.ACK:
                    return True
        return False

    def _is_eof(self, received_telegrams: list[str]) -> bool:
        """Check if any telegram is an EOF response"""
        for response in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(response)
                if reply_telegram.system_function == SystemFunction.EOF:
                    return True
        return False

    def _get_actiontable_data(self, received_telegrams: list[str]) -> Optional[bytes]:
        """Extract actiontable data from received telegrams"""
        for telegram in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(telegram)
                # Look for F17D (TABLE) responses containing actiontable data
                if (
                    reply_telegram.system_function
                    and reply_telegram.system_function.value == "17D"
                ):
                    # Extract the data portion and decode from base64-like format
                    data_portion = reply_telegram.raw_telegram[
                        16:-2
                    ]  # Remove header and checksum
                    # Convert from telegram format to bytes
                    return self._decode_telegram_data(data_portion)
        return None

    def _decode_telegram_data(self, data_str: str) -> bytes:
        """Decode telegram data string to bytes"""
        # Convert A-P encoded string to bytes (similar to existing nibble decoding)
        try:
            # For now, use a simple approach - convert hex-like string to bytes
            # This may need adjustment based on actual telegram format
            result = bytearray()
            for i in range(0, len(data_str), 2):
                if i + 1 < len(data_str):
                    # Map A-P to 0-F if needed
                    char1 = data_str[i]
                    char2 = data_str[i + 1]

                    # Convert A-P encoding to 0-F
                    val1 = ord(char1) - ord("A") if char1.isalpha() else int(char1)
                    val2 = ord(char2) - ord("A") if char2.isalpha() else int(char2)

                    byte_val = (val1 << 4) | val2
                    result.append(byte_val)

            return bytes(result)
        except (ValueError, IndexError):
            # Fallback: return raw string as bytes
            return data_str.encode("ascii")

    def __enter__(self) -> "ActionTableService":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[Exception],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit"""
        # ConbusService handles connection cleanup automatically
        pass
