# Copyright (c) 2025 ldvchosal
"""Unit tests for Conbus client send models."""

from datetime import UTC, datetime

from xp.models import (
    ConbusClientConfig,
    ConbusConnectionStatus,
    ConbusDatapointResponse,
)
from xp.models.conbus.conbus_client_config import ClientConfig

DEFAULT_PORT = 10001
DEFAULT_TIMEOUT = 0.1
CUSTOM_PORT = 8080
CUSTOM_TIMEOUT = 30


class TestTelegramType:
    """Test cases for TelegramType enum."""


class TestConbusClientConfig:
    """Test cases for ConbusClientConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ConbusClientConfig().conbus
        assert config.ip == "192.168.1.100"
        assert config.port == DEFAULT_PORT
        assert config.timeout == DEFAULT_TIMEOUT

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = ClientConfig(ip="10.0.0.1", port=8080, timeout=30)
        assert config.ip == "10.0.0.1"
        assert config.port == CUSTOM_PORT
        assert config.timeout == CUSTOM_TIMEOUT


class TestConbusSendResponse:
    """Test cases for ConbusSendResponse model."""

    def test_successful_response(self) -> None:
        """Test successful response creation."""
        response = ConbusDatapointResponse(
            success=True,
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=["<R0012345011F01DFM>", "<R0012345006F01DFK>"],
        )

        assert response.received_telegrams is not None

        assert response.success is True
        assert response.sent_telegram == "<S0000000000F01D00FA>"
        assert response.received_telegrams == [
            "<R0012345011F01DFM>",
            "<R0012345006F01DFK>",
        ]
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_custom_timestamp(self) -> None:
        """Test response with custom timestamp."""
        custom_time = datetime(2023, 8, 27, 15, 45, 30, tzinfo=UTC)
        response = ConbusDatapointResponse(success=True, timestamp=custom_time)

        assert response.timestamp == custom_time

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        timestamp = datetime(2023, 8, 27, 16, 20, 15, 789123, tzinfo=UTC)
        result = ConbusDatapointResponse(
            success=True,
            sent_telegram="<S0020012521F02D18FM>",
            received_telegrams=["<R0020012521F02D18+23.4C§OK>"],
            timestamp=timestamp,
        ).to_dict()
        assert result["success"] is True
        assert result["sent_telegram"] == "<S0020012521F02D18FM>"
        assert result["received_telegrams"] == ["<R0020012521F02D18+23.4C§OK>"]
        assert result["error"] is None
        assert result["timestamp"] == "2023-08-27T16:20:15.789123+00:00"


class TestConbusConnectionStatus:
    """Test cases for ConbusConnectionStatus model."""

    def test_connected_status(self) -> None:
        """Test connected status creation."""
        last_activity = datetime(2023, 8, 27, 14, 30, 0, tzinfo=UTC)
        status = ConbusConnectionStatus(
            connected=True, ip="192.168.1.100", port=10001, last_activity=last_activity
        )

        assert status.connected is True
        assert status.ip == "192.168.1.100"
        assert status.port == DEFAULT_PORT
        assert status.last_activity == last_activity
        assert status.error is None

    def test_disconnected_status(self) -> None:
        """Test disconnected status creation."""
        status = ConbusConnectionStatus(
            connected=False, ip="192.168.1.100", port=10001, error="Connection timeout"
        )

        assert status.connected is False
        assert status.ip == "192.168.1.100"
        assert status.port == DEFAULT_PORT
        assert status.last_activity is None
        assert status.error == "Connection timeout"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        last_activity = datetime(2023, 8, 27, 18, 45, 20, 456789, tzinfo=UTC)
        result = ConbusConnectionStatus(
            connected=True,
            ip="10.0.0.1",
            port=8080,
            last_activity=last_activity,
            error=None,
        ).to_dict()

        expected = {
            "connected": True,
            "ip": "10.0.0.1",
            "port": 8080,
            "last_activity": "2023-08-27T18:45:20.456789+00:00",
            "error": None,
        }
        assert result == expected


class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_full_workflow_data_models(self) -> None:
        """Test complete workflow with all data models."""
        # Create config
        config = ConbusClientConfig().conbus

        # Create successful response
        response = ConbusDatapointResponse(
            success=True,
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=[
                "<R0012345011F01DFM>",
                "<R0012345006F01DFK>",
                "<R0012345003F01DFN>",
            ],
        )

        # Create connection status
        status = ConbusConnectionStatus(
            connected=True,
            ip=config.ip,
            port=config.port,
            last_activity=datetime.now(UTC),
        )

        # Verify all models work together
        assert config.ip == status.ip
        assert config.port == status.port
        assert response.success is True
        expected_telegram_count = 3
        assert response.received_telegrams is not None
        assert len(response.received_telegrams) == expected_telegram_count
        assert status.connected is True

    def test_error_scenario_workflow(self) -> None:
        """Test error scenario workflow."""
        # Create request

        # Create failed response
        response = ConbusDatapointResponse(success=False, error="Device not found")

        # Create disconnected status
        status = ConbusConnectionStatus(
            connected=False, ip="192.168.1.100", port=10001, error="Connection failed"
        )

        # Verify error handling
        assert response.success is False
        assert response.error == "Device not found"
        assert response.sent_telegram is None
        assert response.received_telegrams == []
        assert status.connected is False
        assert status.error == "Connection failed"
