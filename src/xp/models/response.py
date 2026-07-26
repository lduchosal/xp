# Copyright (c) 2025 ldvchosal
"""Response model for structured service responses.

This module provides the Response class used throughout the application for consistent
service response formatting.
"""

from typing import Any

from xp.utils.time_utils import local_now


class Response:
    """Standard response model for service operations.

    Provides consistent structure for all service responses including success status,
    data payload, error messages, and timestamp.
    """

    def __init__(
        self, *, success: bool, data: object, error: str | None = None
    ) -> None:
        """Initialize response.

        Args:
            success: Whether the operation was successful
            data: Response data payload
            error: Error message if operation failed

        """
        self.success = success
        # Payload is dynamic by design: consumers know the concrete type.
        self.data: Any = data
        self.error = error
        self.timestamp = local_now()

    def to_dict(self) -> dict:
        """Convert response to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the response

        """
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }
