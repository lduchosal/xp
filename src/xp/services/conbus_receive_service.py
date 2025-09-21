"""Conbus Receive Service for receiving telegrams from Conbus servers.

This service extends the base ConbusService to provide receive-only functionality,
allowing clients to receive waiting event telegrams without sending any data.
"""

import logging

from .conbus_service import ConbusService, ConbusError
from ..models.conbus_receive import ConbusReceiveResponse


class ConbusReceiveError(ConbusError):
    """Raised when Conbus receive operations fail"""
    pass


class ConbusReceiveService(ConbusService):
    """
    Service for receiving telegrams from Conbus servers.

    Extends the base ConbusService to provide receive-only functionality
    for collecting waiting event telegrams from the server.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus receive service"""
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)

    def receive_telegrams(self) -> ConbusReceiveResponse:
        """
        Receive waiting telegrams from the Conbus server.

        Connects to the server and receives any waiting event telegrams
        without sending any data first.

        Returns:
            ConbusReceiveResponse: Response containing received telegrams or error
        """
        try:
            if not self.is_connected:
                connect_result = self.connect()
                if not connect_result.success:
                    return ConbusReceiveResponse(
                        success=False,
                        error=f"Failed to connect to server: {connect_result.error}",
                    )

            # Receive responses without sending anything
            responses = self._receive_responses()

            return ConbusReceiveResponse(
                success=True,
                received_telegrams=responses,
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
        self.disconnect()