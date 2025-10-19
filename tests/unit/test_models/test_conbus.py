"""Tests for conbus models."""

from datetime import datetime

from xp.models.conbus.conbus import ConbusRequest, ConbusResponse


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

    def test_post_init_sets_defaults(self):
        """Test __post_init__ sets default values."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        response = ConbusResponse(
            success=True,
            sent_telegrams=["<TEST>"],
            received_telegrams=["<REPLY>"],
            timestamp=timestamp,
        )
        assert response.sent_telegrams == []
        assert response.received_telegrams == []
        assert response.error == ""

    def test_to_dict(self):
        """Test to_dict method."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        result = ConbusResponse(
            success=True,
            sent_telegrams=["<TEST>"],
            received_telegrams=["<REPLY>"],
            error="test error",
            timestamp=timestamp,
        ).to_dict()

        assert result["success"] is True
        assert result["sent_telegrams"] == []  # post_init resets these
        assert result["received_telegrams"] == []  # post_init resets these
        assert result["error"] == "test error"
        assert "2025" in result["timestamp"]
