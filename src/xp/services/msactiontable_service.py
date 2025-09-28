"""Service for downloading XP24 action tables via Conbus protocol."""

import logging
from contextlib import suppress
from typing import Optional, Any, Union


from . import TelegramService, TelegramParsingError
from .conbus_service import ConbusService, ConbusError
from .msactiontable_xp20_serializer import Xp20MsActionTableSerializer
from .msactiontable_xp24_serializer import Xp24MsActionTableSerializer
from .msactiontable_xp33_serializer import Xp33MsActionTableSerializer
from ..models.system_function import SystemFunction
from ..models.msactiontable_xp20 import Xp20MsActionTable
from ..models.msactiontable_xp24 import Xp24MsActionTable
from ..models.msactiontable_xp33 import Xp33MsActionTable


class MsActionTableError(Exception):
    """Raised when XP24 action table operations fail"""

    pass


class MsActionTableService:
    """Service for downloading XP24 action tables via Conbus"""

    def __init__(self, config_path: str = "cli.yml"):
        self.conbus_service = ConbusService(config_path)
        self.serializer = Xp24MsActionTableSerializer()
        self.telegram_service = TelegramService()
        self.logger = logging.getLogger(__name__)

    def download_action_table(
        self, serial_number: str, xpmoduletype: str
    ) -> Union[Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable]:
        """Download action table from XP module"""
        try:
            msactiontable_received = False
            eof_received = False
            msactiontable_telegrams: list[str] = []

            # Usage
            def on_data_received(telegrams: list[str]) -> None:

                nonlocal msactiontable_received, msactiontable_telegrams, eof_received

                self.logger.debug(f"Data received telegrams: {telegrams}")

                if self._is_eof(telegrams):
                    self.logger.debug("Received eof")
                    eof_received = True

                msactiontable_telegram = self._get_msactiontable_telegram(telegrams)
                if msactiontable_telegram is not None:
                    msactiontable_received = True
                    msactiontable_telegrams.append(msactiontable_telegram)
                    self.logger.debug("Received msactiontable_telegram")

                if msactiontable_received:
                    msactiontable_received = False
                    self.conbus_service.send_telegram(
                        serial_number,
                        SystemFunction.ACK,  # F18
                        "00",  # MS action table query
                        on_data_received,
                    )
                    return

                if not eof_received:
                    self.conbus_service.receive_responses(0.01, on_data_received)

            # Send F13 query to request MS action table
            self.conbus_service.send_telegram(
                serial_number,
                SystemFunction.DOWNLOAD_MSACTIONTABLE,  # F13
                "00",  # MS action table query
                on_data_received,
            )

            # Deserialize from received telegrams
            self.logger.debug(
                f"Received msactiontable_telegrams: {msactiontable_telegrams}"
            )
            if not msactiontable_telegrams:
                raise MsActionTableError("No msactiontable telegrams")

            msactiontable_telegram = msactiontable_telegrams[0]
            self.logger.debug(f"Deserialize {xpmoduletype}: {msactiontable_telegram}")

            if xpmoduletype == "xp20":
                return Xp20MsActionTableSerializer.from_telegrams(
                    msactiontable_telegram
                )
            elif xpmoduletype == "xp24":
                return Xp24MsActionTableSerializer.from_telegrams(
                    msactiontable_telegram
                )
            elif xpmoduletype == "xp33":
                return Xp33MsActionTableSerializer.from_telegrams(
                    msactiontable_telegram
                )
            else:
                raise MsActionTableError(f"Unsupported module type: {xpmoduletype}")

        except ConbusError as e:
            raise MsActionTableError(f"Conbus communication failed: {e}") from e

    def _is_eof(self, received_telegrams: list[str]) -> bool:

        for response in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(response)
                if reply_telegram.system_function == SystemFunction.EOF:
                    return True

        return False

    def _get_msactiontable_telegram(
        self, received_telegrams: list[str]
    ) -> Optional[str]:

        for telegram in received_telegrams:
            with suppress(TelegramParsingError):
                reply_telegram = self.telegram_service.parse_reply_telegram(telegram)
                if reply_telegram.system_function == SystemFunction.MSACTIONTABLE:
                    return reply_telegram.raw_telegram

        return None

    def __enter__(self) -> "MsActionTableService":
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
