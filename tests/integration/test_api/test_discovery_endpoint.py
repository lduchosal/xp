"""Integration tests for discovery API endpoint."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from xp.api.main import create_app
from xp.models import ConbusDatapointRequest, ConbusDatapointResponse, DatapointTypeName
from xp.services.conbus_datapoint_service import ConbusDatapointError


@pytest.fixture
def client():
    """Create test client for API."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_successful_response():
    """Mock successful discovery response."""
    return ConbusDatapointResponse(
        success=True,
        request=ConbusDatapointRequest(datapoint_type=DatapointTypeName.UNKNOWN),
        sent_telegram="<S0000000000F01D00FA>",
        received_telegrams=[
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>"
        ],
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_telegram_objects():
    """Mock parsed telegram objects."""
    telegrams = []
    for serial in ["0020030837", "0020044966", "0020042796"]:
        telegram = Mock()
        telegram.telegram_type = 'REPLY'
        telegram.serial_number = serial
        telegrams.append(telegram)
    return telegrams


class TestDiscoveryEndpoint:
    """Test cases for the discovery endpoint."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "xp-api"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "XP Protocol API"
        assert "version" in data
        assert data["docs"] == "/docs"

    @patch('xp.api.routers.conbus.ConbusDatapointService')
    def test_connection_timeout_error(self, mock_service_class, client):
        """Test connection timeout handling."""
        # Mock service to raise timeout error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock failed response with timeout
        failed_response = ConbusDatapointResponse(
            success=False,
            request=ConbusDatapointRequest(datapoint_type=DatapointTypeName.UNKNOWN),
            error="Connection timeout after 10 seconds"
        )
        mock_service.send_telegram.return_value = failed_response

        # Make request
        response = client.post("/api/xp/conbus/discover", json={})

        # Verify error response
        assert response.status_code == 500  # Request Timeout
        data = response.json()
        assert data["success"] is False
        assert "timeout" in data["error"].lower()

    @patch('xp.api.routers.conbus.ConbusDatapointService')
    def test_connection_error(self, mock_service_class, client):
        """Test connection error handling."""
        # Mock service to raise connection error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock failed response with connection error
        failed_response = ConbusDatapointResponse(
            success=False,
            request=ConbusDatapointRequest(datapoint_type=DatapointTypeName.UNKNOWN),
            error="Unable to connect to 192.168.1.100:2113"
        )
        mock_service.send_telegram.return_value = failed_response

        # Make request
        response = client.post("/api/xp/conbus/discover", json={})

        # Verify error response
        assert response.status_code == 500  # Bad Request
        data = response.json()
        assert data["success"] is False
        assert "connect" in data["error"].lower()

    @patch('xp.api.routers.conbus.ConbusDatapointService')
    def test_service_exception_handling(self, mock_service_class, client):
        """Test handling of service exceptions."""
        # Mock service to raise ConbusClientSendError
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.send_telegram.side_effect = ConbusDatapointError("Socket connection failed")

        # Make request
        response = client.post("/api/xp/conbus/discover", json={})

        # Verify error response
        assert response.status_code == 500  # Internal Server Error
        data = response.json()
        assert data["success"] is False
        assert "Socket connection failed" in data["error"]

    @patch('xp.api.routers.conbus.ConbusDatapointService')
    def test_unexpected_exception_handling(self, mock_service_class, client):
        """Test handling of unexpected exceptions."""
        # Mock service to raise unexpected exception
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.send_telegram.side_effect = Exception("Unexpected error")

        # Make request
        response = client.post("/api/xp/conbus/discover", json={})

        # Verify error response
        assert response.status_code == 500  # Internal Server Error
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]

    @patch('xp.api.routers.conbus.ConbusDatapointService')
    def test_empty_discovery_response(self, mock_service_class, client):
        """Test discovery with no devices found."""
        # Mock service with empty response
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        empty_response = ConbusDatapointResponse(
            success=True,
            request=ConbusDatapointRequest(datapoint_type=DatapointTypeName.UNKNOWN),
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=[],
            timestamp=datetime.now()
        )
        mock_service.send_telegram.return_value = empty_response

        # Make request
        response = client.post("/api/xp/conbus/discover", json={})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["received_telegrams"]) == 0
        assert len(data["discovered_devices"]) == 0

    @patch('xp.api.routers.conbus.ConbusDatapointService')
    def test_partial_telegram_parsing_failure(self, mock_service_class, client, mock_successful_response):
        """Test handling when some telegrams fail to parse."""
        # Mock the service instance
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.send_telegram.return_value = mock_successful_response

        # Mock telegram service with partial failures
        mock_telegram_service_instance = Mock()
        mock_telegram_service.return_value = mock_telegram_service_instance

        def mock_parse_telegram(telegram_str):
            if "R0020030837" in telegram_str:
                # Successful parse
                result = Mock()
                result.success = True
                result.data = Mock()
                result.data.telegram_type = 'REPLY'
                result.data.serial_number = "0020030837"
                return result
            else:
                # Failed parse
                result = Mock()
                result.success = False
                return result

        mock_telegram_service_instance.parse_telegram.side_effect = mock_parse_telegram

        # Make request
        response = client.post("/api/xp/conbus/discover", json={})

        # Verify response - should only include successfully parsed devices
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["received_telegrams"]) == 3  # All received
        assert len(data["discovered_devices"]) == 1  # Only successfully parsed
        assert data["discovered_devices"][0]["serial"] == "0020030837"