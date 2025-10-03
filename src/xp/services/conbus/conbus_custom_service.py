"""Conbus Client Send Service for TCP communication with Conbus servers.

This service implements a TCP client that connects to Conbus servers and sends
various types of telegrams including discover, version, and sensor data requests.
"""

import logging

from xp.models.conbus.conbus_custom import ConbusCustomResponse
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.services.conbus.conbus_service import ConbusService
from xp.services.telegram.telegram_service import TelegramService


class ConbusCustomError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusCustomService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        conbus_service: ConbusService,
    ):
        """Initialize the Conbus client send service"""

        # Service dependencies
        self.telegram_service = telegram_service
        self.conbus_service = conbus_service

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def send_custom_telegram(
        self, serial_number: str, function_code: str, data: str
    ) -> ConbusCustomResponse:
        """Send a telegram to the Conbus server"""
        # Generate custom system telegram: <S{serial}F{function}{data}{checksum}>
        telegram_body = f"S{serial_number}F{function_code}D{data}"

        # Send telegram
        response = self.conbus_service.send_telegram_body(telegram_body)
        reply_telegram = None
        if (
            response.received_telegrams is not None
            and len(response.received_telegrams) > 0
        ):
            telegram = response.received_telegrams[0]
            parsed_telegram = self.telegram_service.parse_telegram(telegram)
            if isinstance(parsed_telegram, ReplyTelegram):
                reply_telegram = parsed_telegram

        return ConbusCustomResponse(
            success=response.success,
            serial_number=serial_number,
            function_code=function_code,
            data=data,
            sent_telegram=response.sent_telegram,
            received_telegrams=response.received_telegrams,
            reply_telegram=reply_telegram,
            error=response.error,
        )

    def __enter__(self) -> "ConbusCustomService":
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object | None,
    ) -> None:
        # Cleanup logic if needed
        pass
