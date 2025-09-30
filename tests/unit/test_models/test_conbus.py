"""Tests for conbus models."""

from datetime import datetime

from xp.models.conbus import ConbusRequest, ConbusResponse


class TestConbusRequest:
    """Test ConbusRequest model."""

    def test_to_dict(self):
        """Test to_dict method."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        result = ConbusRequest(
            serial_number="12345",
            function_code="F",
            data="test_data",
            timestamp=timestamp,
        ).to_dict()
        assert result["serial_number"] == "12345"
        assert result["function_code"] == "F"
        assert result["data"] == "test_data"
        assert "2025-01-01T12:00:00" in result["timestamp"]

    def test_post_init_sets_timestamp(self):
        """Test __post_init__ sets timestamp if None."""
        request = ConbusRequest(
            serial_number="12345", function_code="F", data="test", timestamp=None
        )
        assert request.timestamp is not None
        assert isinstance(request.timestamp, datetime)


class TestConbusResponse:
    """Test ConbusResponse model."""

    def test_post_init_sets_default_received_telegrams(self):
        """Test __post_init__ sets default received_telegrams."""
        request = ConbusRequest(serial_number="12345", function_code="F", data="test")
        response = ConbusResponse(success=True, request=request)
        assert response.received_telegrams == []

    def test_to_dict(self):
        """Test to_dict method."""
        request = ConbusRequest(serial_number="12345", function_code="F", data="test")
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        result = ConbusResponse(
            success=True,
            request=request,
            sent_telegram="<TEST>",
            received_telegrams=["<REPLY>"],
            error=None,
            timestamp=timestamp,
        ).to_dict()
        assert result["success"] is True
        assert result["sent_telegram"] == "<TEST>"
        assert result["received_telegrams"] == ["<REPLY>"]
        assert "2025-01-01T12:00:00" in result["timestamp"]
