"""Conbus Receive Service for receiving telegrams from Conbus servers.

This service uses composition with ConbusService to provide receive-only functionality,
allowing clients to receive waiting event telegrams using empty telegram sends.
"""

import logging

from .conbus_service import ConbusService, ConbusError
from ..models.conbus_receive import ConbusReceiveResponse


class ConbusReceiveError(ConbusError):
    """Raised when Conbus receive operations fail"""
    pass


class ConbusReceiveService:
    """
    Service for receiving telegrams from Conbus servers.

    Uses composition with ConbusService to provide receive-only functionality
    for collecting waiting event telegrams from the server.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus receive service"""
        self.conbus_service = ConbusService(config_path)
        self.logger = logging.getLogger(__name__)

    def receive_telegrams(self) -> ConbusReceiveResponse:
        """
        Receive waiting telegrams from the Conbus server.

        Uses send_raw_telegram with empty string to connect and receive
        any waiting event telegrams from the server.

        Returns:
            ConbusReceiveResponse: Response containing received telegrams or error
        """
        try:
            # Send empty telegram to trigger receive operation
            response = self.conbus_service.send_raw_telegram("")

            if not response.success:
                return ConbusReceiveResponse(
                    success=False,
                    error=response.error,
                )

            return ConbusReceiveResponse(
                success=True,
                received_telegrams=response.received_telegrams or [],
            )

        except Exception as e:
            error_msg = f"Failed to receive telegrams: {e}"
            self.logger.error(error_msg)
            return ConbusReceiveResponse(
                success=False,
                error=error_msg,
            )

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
