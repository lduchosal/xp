"""Tests for conbus discover model."""

from datetime import datetime

from xp.models.conbus_discover import ConbusDiscoverResponse


class TestConbusDiscoverResponse:
    """Test ConbusDiscoverResponse model."""

    def test_post_init_sets_timestamp(self):
        """Test __post_init__ sets timestamp if None."""
        response = ConbusDiscoverResponse(success=True)
        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)

    def test_post_init_sets_received_telegrams(self):
        """Test __post_init__ sets empty list for received_telegrams."""
        response = ConbusDiscoverResponse(success=True)
        assert response.received_telegrams == []

    def test_to_dict(self):
        """Test to_dict method."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        result = ConbusDiscoverResponse(
            success=True,
            sent_telegram="<DISCOVER>",
            received_telegrams=["<REPLY1>", "<REPLY2>"],
            discovered_devices=["device1", "device2"],
            error=None,
            timestamp=timestamp,
        ).to_dict()
        assert result["success"] is True
        assert result["sent_telegram"] == "<DISCOVER>"
        assert result["received_telegrams"] == ["<REPLY1>", "<REPLY2>"]
        assert result["discovered_devices"] == ["device1", "device2"]
        assert result["error"] is None
        assert "2025-01-01T12:00:00" in result["timestamp"]

    def test_to_dict_with_error(self):
        """Test to_dict with error."""
        result = ConbusDiscoverResponse(
            success=False, error="Connection failed", timestamp=datetime(2025, 1, 1)
        ).to_dict()
        assert result["success"] is False
        assert result["error"] == "Connection failed"
