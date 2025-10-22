"""Tests for conbus discover model."""

from datetime import datetime

from xp.models.conbus.conbus_discover import ConbusDiscoverResponse


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
            discovered_devices=[
                {
                    "serial_number": "device1",
                    "module_type": "XP",
                    "module_type_code": 7,
                    "module_type_name": "XP24",
                },
                {
                    "serial_number": "device2",
                    "module_type": "XP",
                    "module_type_code": 10,
                    "module_type_name": "XP24P",
                },
            ],
            error=None,
            timestamp=timestamp,
        ).to_dict()
        assert result["success"] is True
        assert result["sent_telegram"] == "<DISCOVER>"
        assert result["received_telegrams"] == ["<REPLY1>", "<REPLY2>"]
        assert result["discovered_devices"] == [
            {
                "serial_number": "device1",
                "module_type": "XP",
                "module_type_code": 7,
                "module_type_name": "XP24",
            },
            {
                "serial_number": "device2",
                "module_type": "XP",
                "module_type_code": 10,
                "module_type_name": "XP24P",
            },
        ]
        assert result["error"] is None
        assert "2025-01-01T12:00:00" in result["timestamp"]

    def test_to_dict_with_error(self):
        """Test to_dict with error."""
        result = ConbusDiscoverResponse(
            success=False, error="Connection failed", timestamp=datetime(2025, 1, 1)
        ).to_dict()
        assert result["success"] is False
        assert result["error"] == "Connection failed"
