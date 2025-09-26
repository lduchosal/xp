"""Conbus Raw Service for sending raw telegram sequences.

This service handles sending raw telegram strings without prior validation.
"""

import logging
from typing import Optional, Any

from .conbus_service import ConbusService
from ..models.conbus_raw import ConbusRawResponse


class ConbusRawError(Exception):
    """Raised when Conbus raw operations fail"""

    pass


class ConbusRawService:
    """
    Service for sending raw telegram sequences to Conbus servers.

    Handles parsing and sending of raw telegram strings without validation.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus raw service"""
        self.conbus_service = ConbusService(config_path)
        self.logger = logging.getLogger(__name__)

    def send_raw_telegrams(self, raw_input: str) -> ConbusRawResponse:
        """
        Send raw telegram sequence to Conbus server.

        Args:
            raw_input: Raw string containing one or more telegrams

        Returns:
            ConbusRawResponse containing results
        """
        try:

            self.logger.info(f"Sending raw telegram: {raw_input}")

            response = self.conbus_service.send_raw_telegram(raw_input)

            if not response.success:
                return ConbusRawResponse(
                    success=False,
                    sent_telegrams=raw_input,
                    error=f"Failed to send telegram {raw_input}: {response.error}",
                )

            return ConbusRawResponse(
                success=True,
                sent_telegrams=raw_input,
                received_telegrams=response.received_telegrams,
            )

        except Exception as e:
            error_msg = f"Failed to send raw telegrams: {e}"
            self.logger.error(error_msg)
            return ConbusRawResponse(success=False, error=error_msg)

    def __enter__(self) -> "ConbusRawService":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit - ensure connection is closed"""
        self.conbus_service.disconnect()
