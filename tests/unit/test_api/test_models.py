"""Unit tests for API models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from xp.api.models.discovery import (
    DiscoveryRequest,
    DeviceInfo,
    DiscoveryRequestInfo,
    DiscoveryResponse,
    DiscoveryErrorResponse,
)


class TestDiscoveryRequest:
    """Test cases for DiscoveryRequest model."""

    def test_empty_request_is_valid(self):
        """Test that empty request body is valid."""
        request = DiscoveryRequest()
        assert request is not None

    def test_request_serialization(self):
        """Test request serialization to dict."""
        request = DiscoveryRequest()
        data = request.model_dump()
        assert isinstance(data, dict)


class TestDeviceInfo:
    """Test cases for DeviceInfo model."""

    def test_valid_device_info(self):
        """Test creating valid device info."""
        device = DeviceInfo(
            serial="0020030837",
            telegram="<R0020030837F01DFM>"
        )
        assert device.serial == "0020030837"
        assert device.telegram == "<R0020030837F01DFM>"

    def test_device_info_serialization(self):
        """Test device info serialization."""
        device = DeviceInfo(
            serial="0020030837",
            telegram="<R0020030837F01DFM>"
        )
        data = device.model_dump()
        expected = {
            "serial": "0020030837",
            "telegram": "<R0020030837F01DFM>"
        }
        assert data == expected

    def test_missing_serial_raises_error(self):
        """Test that missing serial raises validation error."""
        with pytest.raises(ValidationError):
            DeviceInfo(telegram="<R0020030837F01DFM>")

    def test_missing_telegram_raises_error(self):
        """Test that missing telegram raises validation error."""
        with pytest.raises(ValidationError):
            DeviceInfo(serial="0020030837")


class TestDiscoveryRequestInfo:
    """Test cases for DiscoveryRequestInfo model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        request_info = DiscoveryRequestInfo()
        assert request_info.telegram_type == "DISCOVERY"
        assert request_info.target_serial is None

    def test_custom_values(self):
        """Test setting custom values."""
        request_info = DiscoveryRequestInfo(
            telegram_type="CUSTOM",
            target_serial="1234567890"
        )
        assert request_info.telegram_type == "CUSTOM"
        assert request_info.target_serial == "1234567890"


class TestDiscoveryResponse:
    """Test cases for DiscoveryResponse model."""

    def test_minimal_response(self):
        """Test creating minimal successful response."""
        request_info = DiscoveryRequestInfo()
        response = DiscoveryResponse(
            request=request_info,
            sent_telegram="<S0000000000F01D00FA>"
        )
        assert response.success is True
        assert response.request == request_info
        assert response.sent_telegram == "<S0000000000F01D00FA>"
        assert response.received_telegrams == []
        assert response.discovered_devices == []
        assert response.timestamp is not None

    def test_full_response(self):
        """Test creating full response with devices."""
        request_info = DiscoveryRequestInfo()
        devices = [
            DeviceInfo(serial="0020030837", telegram="<R0020030837F01DFM>"),
            DeviceInfo(serial="0020044966", telegram="<R0020044966F01DFK>")
        ]
        received_telegrams = ["<R0020030837F01DFM>", "<R0020044966F01DFK>"]

        response = DiscoveryResponse(
            request=request_info,
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=received_telegrams,
            discovered_devices=devices
        )

        assert response.success is True
        assert len(response.discovered_devices) == 2
        assert len(response.received_telegrams) == 2
        assert response.discovered_devices[0].serial == "0020030837"

    def test_response_serialization(self):
        """Test response serialization matches specification."""
        request_info = DiscoveryRequestInfo()
        devices = [
            DeviceInfo(serial="0020030837", telegram="<R0020030837F01DFM>")
        ]

        response = DiscoveryResponse(
            request=request_info,
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=["<R0020030837F01DFM>"],
            discovered_devices=devices,
            timestamp="2024-01-15T10:30:45.123Z"
        )

        data = response.model_dump()
        assert data["success"] is True
        assert data["request"]["telegram_type"] == "DISCOVERY"
        assert data["request"]["target_serial"] is None
        assert data["sent_telegram"] == "<S0000000000F01D00FA>"
        assert len(data["received_telegrams"]) == 1
        assert len(data["discovered_devices"]) == 1
        assert data["discovered_devices"][0]["serial"] == "0020030837"
        assert data["timestamp"] == "2024-01-15T10:30:45.123Z"

    def test_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        before = datetime.now()
        response = DiscoveryResponse(
            request=DiscoveryRequestInfo(),
            sent_telegram="<S0000000000F01D00FA>"
        )
        after = datetime.now()

        # Parse the ISO timestamp
        timestamp = datetime.fromisoformat(response.timestamp.replace('Z', '+00:00'))
        # Remove timezone info for comparison
        timestamp = timestamp.replace(tzinfo=None)

        assert before <= timestamp <= after


class TestDiscoveryErrorResponse:
    """Test cases for DiscoveryErrorResponse model."""

    def test_error_response(self):
        """Test creating error response."""
        error_response = DiscoveryErrorResponse(
            error="Connection timeout: Unable to connect to 192.168.1.100:2113"
        )
        assert error_response.success is False
        assert "Connection timeout" in error_response.error
        assert error_response.timestamp is not None

    def test_error_response_serialization(self):
        """Test error response serialization."""
        error_response = DiscoveryErrorResponse(
            error="Internal server error: Socket connection failed",
            timestamp="2024-01-15T10:30:45.123Z"
        )

        data = error_response.model_dump()
        assert data["success"] is False
        assert data["error"] == "Internal server error: Socket connection failed"
        assert data["timestamp"] == "2024-01-15T10:30:45.123Z"

    def test_missing_error_raises_validation_error(self):
        """Test that missing error message raises validation error."""
        with pytest.raises(ValidationError):
            DiscoveryErrorResponse()

    def test_timestamp_auto_generation_for_error(self):
        """Test that timestamp is automatically generated for error response."""
        before = datetime.now()
        error_response = DiscoveryErrorResponse(error="Test error")
        after = datetime.now()

        # Parse the ISO timestamp
        timestamp = datetime.fromisoformat(error_response.timestamp.replace('Z', '+00:00'))
        # Remove timezone info for comparison
        timestamp = timestamp.replace(tzinfo=None)

        assert before <= timestamp <= after