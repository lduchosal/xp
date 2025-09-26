"""Conbus Receive Service for receiving telegrams from Conbus servers.

This service uses composition with ConbusService to provide receive-only functionality,
allowing clients to receive waiting event telegrams using empty telegram sends.
"""

import logging
from typing import Optional, Any

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

    def receive_telegrams(self, timeout: float = 2.0) -> ConbusReceiveResponse:
        """
        Receive waiting telegrams from the Conbus server.

        Uses send_raw_telegram with empty string to connect and receive
        any waiting event telegrams from the server.

        Args:
            timeout: Timeout in seconds for receiving telegrams (default: 2.0)

        Returns:
            ConbusReceiveResponse: Response containing received telegrams or error
        """
        try:
            # Send empty telegram to trigger receive operation
            response = self.conbus_service.receive_responses(timeout=timeout)
            return ConbusReceiveResponse(
                success=True,
                received_telegrams=response,
            )

        except Exception as e:
            error_msg = f"Failed to receive telegrams: {e}"
            self.logger.error(error_msg)
            return ConbusReceiveResponse(
                success=False,
                error=error_msg,
            )

    def __enter__(self) -> "ConbusReceiveService":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit - ensure connection is closed"""
