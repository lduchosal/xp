"""Tests for connection module initialization."""

import xp.connection as connection_module
from xp.connection import ProtocolError, ValidationError, XPError


class TestConnectionInit:
    """Test connection module initialization."""

    def test_xp_error_imported(self):
        """Test XPError is importable from connection module."""
        assert hasattr(connection_module, "XPError")
        assert connection_module.XPError is XPError

    def test_protocol_error_imported(self):
        """Test ProtocolError is importable from connection module."""
        assert hasattr(connection_module, "ProtocolError")
        assert connection_module.ProtocolError is ProtocolError

    def test_validation_error_imported(self):
        """Test ValidationError is importable from connection module."""
        assert hasattr(connection_module, "ValidationError")
        assert connection_module.ValidationError is ValidationError

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        expected = ["XPError", "ProtocolError", "ValidationError"]
        assert connection_module.__all__ == expected

    def test_all_members_accessible(self):
        """Test all members in __all__ are accessible."""
        for member in connection_module.__all__:
            assert hasattr(connection_module, member)
