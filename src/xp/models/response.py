"""Response model for structured service responses.

This module provides the Response class used throughout the application
for consistent service response formatting.
"""

from datetime import datetime
from typing import Any, Optional


class Response:
    """Standard response model for service operations.

    Provides consistent structure for all service responses including
    success status, data payload, error messages, and timestamp.
    """

    def __init__(self, success: bool, data: Any, error: Optional[str] = None):
        """Initialize response.

        Args:
            success: Whether the operation was successful
            data: Response data payload
            error: Error message if operation failed
        """
        self.success = success
        self.data = data
        self.error = error
        self.timestamp = datetime.now()

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
