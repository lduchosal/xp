"""Connection-related exceptions for XP CLI tool.

Following the architecture requirement for structured error handling.
"""


class XPError(Exception):
    """Base exception for XP CLI tool."""

    pass


class ProtocolError(XPError):
    """Console bus protocol errors."""

    pass


class ValidationError(XPError):
    """Input validation errors."""

    pass
