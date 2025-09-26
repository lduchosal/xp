"""Conbus Link Number Service for setting module link numbers.

This service handles setting link numbers for modules through Conbus telegrams.
"""

import logging
from typing import Any, Optional

from . import TelegramService
from .conbus_service import ConbusService
from .telegram_link_number_service import LinkNumberService, LinkNumberError
from ..models.conbus_linknumber import ConbusLinknumberResponse
from ..models.reply_telegram import ReplyTelegram


class ConbusLinknumberService:
    """
    Service for setting module link numbers via Conbus telegrams.

    Handles link number assignment by sending F04D04 telegrams and processing
    ACK/NAK responses from modules.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus link number service"""

        # Service dependencies
        self.conbus_service = ConbusService(config_path)
        self.link_number_service = LinkNumberService()
        self.telegram_service = TelegramService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> "ConbusLinknumberService":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        # Cleanup logic if needed
        pass

    def set_linknumber(
        self, serial_number: str, link_number: int
    ) -> ConbusLinknumberResponse:
        """
        Set the link number for a specific module.

        Args:
            serial_number: 10-digit module serial number
            link_number: Link number to set (0-99)

        Returns:
            ConbusLinknumberResponse with operation result

        Raises:
            LinkNumberError: If parameters are invalid
        """
        try:
            # Generate the link number setting telegram
            telegram = self.link_number_service.generate_set_link_number_telegram(
                serial_number, link_number
            )

            # Send telegram using ConbusService
            with self.conbus_service:
                response = self.conbus_service.send_raw_telegram(telegram)

                # Determine result based on response
                result = "NAK"  # Default to NAK
                if response.success and response.received_telegrams:
                    # Try to parse the first received telegram
                    if len(response.received_telegrams) > 0:
                        received_telegram = response.received_telegrams[0]
                        try:
                            parsed_telegram = self.telegram_service.parse_telegram(
                                received_telegram
                            )
                            if isinstance(parsed_telegram, ReplyTelegram):
                                if self.link_number_service.is_ack_response(
                                    parsed_telegram
                                ):
                                    result = "ACK"
                                elif self.link_number_service.is_nak_response(
                                    parsed_telegram
                                ):
                                    result = "NAK"
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to parse reply telegram: {e}"
                            )

                return ConbusLinknumberResponse(
                    success=response.success and result == "ACK",
                    result=result,
                    serial_number=serial_number,
                    sent_telegram=telegram,
                    received_telegrams=response.received_telegrams,
                    error=response.error,
                    timestamp=response.timestamp,
                )

        except LinkNumberError as e:
            return ConbusLinknumberResponse(
                success=False,
                result="NAK",
                serial_number=serial_number,
                error=str(e),
            )
        except Exception as e:
            return ConbusLinknumberResponse(
                success=False,
                result="NAK",
                serial_number=serial_number,
                error=f"Unexpected error: {str(e)}",
            )