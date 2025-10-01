"""Tests for connection exceptions."""

import pytest

from xp.connection.exceptions import ProtocolError, ValidationError, XPError


class TestXPError:
    """Test XPError base exception."""

    def test_xp_error_is_exception(self):
        """Test XPError inherits from Exception."""
        assert issubclass(XPError, Exception)

    def test_xp_error_can_be_raised(self):
        """Test XPError can be raised."""
        with pytest.raises(XPError):
            raise XPError("Test error")

    def test_xp_error_with_message(self):
        """Test XPError with custom message."""
        msg = "Custom error message"
        with pytest.raises(XPError) as exc_info:
            raise XPError(msg)
        assert str(exc_info.value) == msg

    def test_xp_error_without_message(self):
        """Test XPError without message."""
        with pytest.raises(XPError):
            raise XPError()


class TestProtocolError:
    """Test ProtocolError exception."""

    def test_protocol_error_inherits_from_xp_error(self):
        """Test ProtocolError inherits from XPError."""
        assert issubclass(ProtocolError, XPError)

    def test_protocol_error_is_exception(self):
        """Test ProtocolError is also an Exception."""
        assert issubclass(ProtocolError, Exception)

    def test_protocol_error_can_be_raised(self):
        """Test ProtocolError can be raised."""
        with pytest.raises(ProtocolError):
            raise ProtocolError("Protocol error")

    def test_protocol_error_with_message(self):
        """Test ProtocolError with custom message."""
        msg = "Invalid protocol format"
        with pytest.raises(ProtocolError) as exc_info:
            raise ProtocolError(msg)
        assert str(exc_info.value) == msg

    def test_protocol_error_caught_as_xp_error(self):
        """Test ProtocolError can be caught as XPError."""
        with pytest.raises(XPError):
            raise ProtocolError("Protocol error")


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_inherits_from_xp_error(self):
        """Test ValidationError inherits from XPError."""
        assert issubclass(ValidationError, XPError)

    def test_validation_error_is_exception(self):
        """Test ValidationError is also an Exception."""
        assert issubclass(ValidationError, Exception)

    def test_validation_error_can_be_raised(self):
        """Test ValidationError can be raised."""
        with pytest.raises(ValidationError):
            raise ValidationError("Validation failed")

    def test_validation_error_with_message(self):
        """Test ValidationError with custom message."""
        msg = "Invalid input data"
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(msg)
        assert str(exc_info.value) == msg

    def test_validation_error_caught_as_xp_error(self):
        """Test ValidationError can be caught as XPError."""
        with pytest.raises(XPError):
            raise ValidationError("Validation error")
