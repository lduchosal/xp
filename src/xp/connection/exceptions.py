"""
Connection-related exceptions for XP CLI tool.
Following the architecture requirement for structured error handling.
"""


class XPError(Exception):
    """Base exception for XP CLI tool"""
    pass


class ConnectionError(XPError):
    """TCP connection related errors"""
    pass


class ProtocolError(XPError):
    """Console bus protocol errors"""
    pass


class ValidationError(XPError):
    """Input validation errors"""
    pass


class ModuleNotFoundError(XPError):
    """Module not found on remote bus"""
    pass