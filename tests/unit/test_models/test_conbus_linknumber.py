from datetime import datetime
from xp.models.conbus_linknumber import ConbusLinknumberResponse


class TestConbusLinknumberResponse:
    """Test cases for ConbusLinknumberResponse model"""

    def test_successful_response(self):
        """Test successful link number response creation"""
        response = ConbusLinknumberResponse(
            success=True,
            result="ACK",
            serial_number="0020045057",
            sent_telegram="<S0020045057F04D0425FO>",
            received_telegrams=["<R0020045057F04D0400FH>"],
        )

        assert response.success is True
        assert response.result == "ACK"
        assert response.serial_number == "0020045057"
        assert response.sent_telegram == "<S0020045057F04D0425FO>"
        assert response.received_telegrams == ["<R0020045057F04D0400FH>"]
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_failed_response(self):
        """Test failed link number response creation"""
        response = ConbusLinknumberResponse(
            success=False,
            result="NAK",
            serial_number="0020045057",
            error="Invalid link number",
        )

        assert response.success is False
        assert response.result == "NAK"
        assert response.serial_number == "0020045057"
        assert response.sent_telegram is None
        assert response.received_telegrams == []
        assert response.error == "Invalid link number"
        assert isinstance(response.timestamp, datetime)

    def test_custom_timestamp(self):
        """Test response with custom timestamp"""
        custom_time = datetime(2025, 9, 26, 13, 11, 25, 820383)
        response = ConbusLinknumberResponse(
            success=True,
            result="ACK",
            serial_number="0020045057",
            timestamp=custom_time,
        )

        assert response.timestamp == custom_time

    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime(2025, 9, 26, 13, 11, 25, 820383)
        response = ConbusLinknumberResponse(
            success=True,
            result="ACK",
            serial_number="0020045057",
            sent_telegram="<S0020045057F04D0425FO>",
            received_telegrams=["<R0020045057F04D0400FH>"],
            timestamp=timestamp,
        )

        result = response.to_dict()
        expected = {
            "success": True,
            "result": "ACK",
            "serial_number": "0020045057",
            "sent_telegram": "<S0020045057F04D0425FO>",
            "received_telegrams": ["<R0020045057F04D0400FH>"],
            "error": None,
            "timestamp": "2025-09-26T13:11:25.820383",
        }
        assert result == expected

    def test_to_dict_with_error(self):
        """Test conversion to dictionary with error"""
        response = ConbusLinknumberResponse(
            success=False,
            result="NAK",
            serial_number="0020045057",
            error="Connection timeout",
        )

        result = response.to_dict()
        assert result["success"] is False
        assert result["result"] == "NAK"
        assert result["serial_number"] == "0020045057"
        assert result["sent_telegram"] is None
        assert result["received_telegrams"] == []
        assert result["error"] == "Connection timeout"
        assert result["timestamp"] is not None

    def test_empty_telegrams_init(self):
        """Test that received_telegrams is initialized as empty list"""
        response = ConbusLinknumberResponse(
            success=True,
            result="ACK",
            serial_number="0020045057",
        )

        assert response.received_telegrams == []