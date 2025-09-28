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
            actiontable_received = False
            eof_received = False
            actiontable_data: list[str] = []

            def on_data_received(telegrams: list[str]) -> None:
                nonlocal actiontable_received, actiontable_data, eof_received

                self.logger.debug(
                    f"Data received telegrams: {telegrams}  actiontable: {actiontable_received}"
                )

                if self._is_eof(telegrams):
                    self.logger.debug("Received EOF")
                    eof_received = True

                table_data = self._get_actiontable_data(telegrams)
                if table_data is not None:
                    self.logger.debug("Received ACTIONTABLE")
                    actiontable_received = True
                    actiontable_data.append(table_data)

                    # Send continue signal to get next chunk
                    self.conbus_service.send_telegram(
                        serial_number,
                        SystemFunction.ACK,  # F18
                        "00",  # Continue signal
                        on_data_received,
                    )

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

            all_datas = "".join(actiontable_data)
            # Deserialize from received data
            return self.serializer.from_encoded_string(all_datas)

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

    def _is_eof(self, received_telegrams: list[str]) -> bool:
        """Check if any telegram is an EOF response"""
        for response in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(response)
                if reply_telegram.system_function == SystemFunction.EOF:
                    return True
        return False

    def _get_actiontable_data(self, received_telegrams: list[str]) -> Optional[str]:
        """Extract actiontable data from received telegrams"""
        for telegram in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(telegram)
                # Look for F17D (TABLE) responses containing actiontable data
                if reply_telegram.system_function == SystemFunction.ACTIONTABLE:
                    # Extract the data portion and decode from base64-like format
                    return reply_telegram.data_value[2:]
        return None

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
