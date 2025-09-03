import pytest
from datetime import datetime
from src.xp.models.conbus_client_send import (
    TelegramType, ConbusClientConfig, ConbusSendRequest, 
    ConbusSendResponse, ConbusConnectionStatus
)


class TestTelegramType:
    """Test cases for TelegramType enum"""
    
    def test_telegram_type_values(self):
        """Test that TelegramType enum has correct values"""
        assert TelegramType.DISCOVERY.value == "discovery"
        assert TelegramType.VERSION.value == "version"
        assert TelegramType.VOLTAGE.value == "voltage"
        assert TelegramType.TEMPERATURE.value == "temperature"
        assert TelegramType.CURRENT.value == "current"
        assert TelegramType.HUMIDITY.value == "humidity"
    
    def test_telegram_type_count(self):
        """Test that all expected telegram types are present"""
        expected_types = {"discovery", "version", "voltage", "temperature", "current", "humidity"}
        actual_types = {t.value for t in TelegramType}
        assert actual_types == expected_types


class TestConbusClientConfig:
    """Test cases for ConbusClientConfig model"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ConbusClientConfig()
        assert config.ip == "192.168.1.100"
        assert config.port == 10001
        assert config.timeout == 10
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = ConbusClientConfig(
            ip="10.0.0.1",
            port=8080,
            timeout=30
        )
        assert config.ip == "10.0.0.1"
        assert config.port == 8080
        assert config.timeout == 30
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = ConbusClientConfig(ip="192.168.1.50", port=9000, timeout=15)
        result = config.to_dict()
        
        expected = {
            "ip": "192.168.1.50",
            "port": 9000,
            "timeout": 15
        }
        assert result == expected


class TestConbusSendRequest:
    """Test cases for ConbusSendRequest model"""
    
    def test_discovery_request(self):
        """Test discovery request creation"""
        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)
        
        assert request.telegram_type == TelegramType.DISCOVERY
        assert request.target_serial is None
        assert request.function_code is None
        assert request.data_point_code is None
        assert isinstance(request.timestamp, datetime)
    
    def test_version_request(self):
        """Test version request creation"""
        request = ConbusSendRequest(
            telegram_type=TelegramType.VERSION,
            target_serial="0020030837"
        )
        
        assert request.telegram_type == TelegramType.VERSION
        assert request.target_serial == "0020030837"
        assert isinstance(request.timestamp, datetime)
    
    def test_sensor_request(self):
        """Test sensor request creation"""
        request = ConbusSendRequest(
            telegram_type=TelegramType.TEMPERATURE,
            target_serial="0020012521"
        )
        
        assert request.telegram_type == TelegramType.TEMPERATURE
        assert request.target_serial == "0020012521"
        assert isinstance(request.timestamp, datetime)
    
    def test_custom_timestamp(self):
        """Test request with custom timestamp"""
        custom_time = datetime(2023, 8, 27, 10, 30, 45)
        request = ConbusSendRequest(
            telegram_type=TelegramType.VOLTAGE,
            target_serial="0020030837",
            timestamp=custom_time
        )
        
        assert request.timestamp == custom_time
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime(2023, 8, 27, 10, 30, 45, 123456)
        request = ConbusSendRequest(
            telegram_type=TelegramType.CURRENT,
            target_serial="0020044974",
            function_code="02",
            data_point_code="21",
            timestamp=timestamp
        )
        
        result = request.to_dict()
        expected = {
            "telegram_type": "current",
            "target_serial": "0020044974",
            "function_code": "02",
            "data_point_code": "21",
            "timestamp": "2023-08-27T10:30:45.123456"
        }
        assert result == expected


class TestConbusSendResponse:
    """Test cases for ConbusSendResponse model"""
    
    def test_successful_response(self):
        """Test successful response creation"""
        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)
        response = ConbusSendResponse(
            success=True,
            request=request,
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=["<R0020030837F01DFM>", "<R0020044966F01DFK>"]
        )
        
        assert response.success is True
        assert response.request == request
        assert response.sent_telegram == "<S0000000000F01D00FA>"
        assert len(response.received_telegrams) == 2
        assert "<R0020030837F01DFM>" in response.received_telegrams
        assert "<R0020044966F01DFK>" in response.received_telegrams
        assert response.error is None
        assert isinstance(response.timestamp, datetime)
    
    def test_failed_response(self):
        """Test failed response creation"""
        request = ConbusSendRequest(telegram_type=TelegramType.VERSION, target_serial="0020030837")
        response = ConbusSendResponse(
            success=False,
            request=request,
            error="Connection timeout"
        )
        
        assert response.success is False
        assert response.request == request
        assert response.sent_telegram is None
        assert response.received_telegrams == []
        assert response.error == "Connection timeout"
        assert isinstance(response.timestamp, datetime)
    
    def test_empty_received_telegrams_initialization(self):
        """Test that received_telegrams is initialized as empty list"""
        request = ConbusSendRequest(telegram_type=TelegramType.HUMIDITY, target_serial="0020012521")
        response = ConbusSendResponse(success=True, request=request)
        
        assert response.received_telegrams == []
        assert isinstance(response.received_telegrams, list)
    
    def test_custom_timestamp(self):
        """Test response with custom timestamp"""
        custom_time = datetime(2023, 8, 27, 15, 45, 30)
        request = ConbusSendRequest(telegram_type=TelegramType.VOLTAGE, target_serial="0020030837")
        response = ConbusSendResponse(
            success=True,
            request=request,
            timestamp=custom_time
        )
        
        assert response.timestamp == custom_time
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime(2023, 8, 27, 16, 20, 15, 789123)
        request = ConbusSendRequest(telegram_type=TelegramType.TEMPERATURE, target_serial="0020012521")
        response = ConbusSendResponse(
            success=True,
            request=request,
            sent_telegram="<S0020012521F02D18FM>",
            received_telegrams=["<R0020012521F02D18+23.4C§OK>"],
            timestamp=timestamp
        )
        
        result = response.to_dict()
        
        assert result["success"] is True
        assert result["sent_telegram"] == "<S0020012521F02D18FM>"
        assert result["received_telegrams"] == ["<R0020012521F02D18+23.4C§OK>"]
        assert result["error"] is None
        assert result["timestamp"] == "2023-08-27T16:20:15.789123"
        assert "request" in result
        assert result["request"]["telegram_type"] == "temperature"


class TestConbusConnectionStatus:
    """Test cases for ConbusConnectionStatus model"""
    
    def test_connected_status(self):
        """Test connected status creation"""
        last_activity = datetime(2023, 8, 27, 14, 30, 0)
        status = ConbusConnectionStatus(
            connected=True,
            ip="192.168.1.100",
            port=10001,
            last_activity=last_activity
        )
        
        assert status.connected is True
        assert status.ip == "192.168.1.100"
        assert status.port == 10001
        assert status.last_activity == last_activity
        assert status.error is None
    
    def test_disconnected_status(self):
        """Test disconnected status creation"""
        status = ConbusConnectionStatus(
            connected=False,
            ip="192.168.1.100",
            port=10001,
            error="Connection timeout"
        )
        
        assert status.connected is False
        assert status.ip == "192.168.1.100"
        assert status.port == 10001
        assert status.last_activity is None
        assert status.error == "Connection timeout"
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        last_activity = datetime(2023, 8, 27, 18, 45, 20, 456789)
        status = ConbusConnectionStatus(
            connected=True,
            ip="10.0.0.1",
            port=8080,
            last_activity=last_activity,
            error=None
        )
        
        result = status.to_dict()
        expected = {
            "connected": True,
            "ip": "10.0.0.1",
            "port": 8080,
            "last_activity": "2023-08-27T18:45:20.456789",
            "error": None
        }
        assert result == expected
    
    def test_to_dict_no_activity(self):
        """Test conversion to dictionary with no last activity"""
        status = ConbusConnectionStatus(
            connected=False,
            ip="192.168.1.50",
            port=9000
        )
        
        result = status.to_dict()
        expected = {
            "connected": False,
            "ip": "192.168.1.50",
            "port": 9000,
            "last_activity": None,
            "error": None
        }
        assert result == expected


class TestModelIntegration:
    """Integration tests for model interactions"""
    
    def test_full_workflow_data_models(self):
        """Test complete workflow with all data models"""
        # Create config
        config = ConbusClientConfig(ip="192.168.1.200", port=10002, timeout=20)
        
        # Create request
        request = ConbusSendRequest(
            telegram_type=TelegramType.DISCOVERY
        )
        
        # Create successful response
        response = ConbusSendResponse(
            success=True,
            request=request,
            sent_telegram="<S0000000000F01D00FA>",
            received_telegrams=["<R0020030837F01DFM>", "<R0020044966F01DFK>", "<R0020042796F01DFN>"]
        )
        
        # Create connection status
        status = ConbusConnectionStatus(
            connected=True,
            ip=config.ip,
            port=config.port,
            last_activity=datetime.now()
        )
        
        # Verify all models work together
        assert config.ip == status.ip
        assert config.port == status.port
        assert request.telegram_type == TelegramType.DISCOVERY
        assert response.success is True
        assert len(response.received_telegrams) == 3
        assert status.connected is True
    
    def test_error_scenario_workflow(self):
        """Test error scenario workflow"""
        # Create request
        request = ConbusSendRequest(
            telegram_type=TelegramType.VERSION,
            target_serial="9999999999"  # Non-existent device
        )
        
        # Create failed response
        response = ConbusSendResponse(
            success=False,
            request=request,
            error="Device not found"
        )
        
        # Create disconnected status
        status = ConbusConnectionStatus(
            connected=False,
            ip="192.168.1.100",
            port=10001,
            error="Connection failed"
        )
        
        # Verify error handling
        assert response.success is False
        assert response.error == "Device not found"
        assert response.sent_telegram is None
        assert response.received_telegrams == []
        assert status.connected is False
        assert status.error == "Connection failed"