import pytest
from unittest.mock import Mock, patch
import socket
from datetime import datetime
from xp.services.conbus_datapoint_service import (
    ConbusDatapointService,
    ConbusDatapointError,
)
from xp.models import (
    ConbusDatapointRequest,
)
from xp.models import ConbusDatapointResponse, DatapointTypeName


class TestConbusDatapointService:
    """Test cases for ConbusDatapointService"""

    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Create a temporary config file for testing"""
        config_file = tmp_path / "test_cli.yml"
        config_content = """
conbus:
  ip: 10.0.0.1
  port: 8080
  timeout: 15
"""
        config_file.write_text(config_content)
        return str(config_file)

    @pytest.fixture
    def service(self, mock_config_file):
        """Create service instance with test config"""
        return ConbusDatapointService(config_path=mock_config_file)

    @pytest.fixture
    def mock_socket(self):
        """Create mock socket for testing"""
        mock_sock = Mock(spec=socket.socket)
        mock_sock.settimeout = Mock()
        mock_sock.connect = Mock()
        mock_sock.send = Mock()
        mock_sock.recv = Mock()
        mock_sock.close = Mock()
        mock_sock.gettimeout = Mock(return_value=10.0)
        return mock_sock


class TestServiceInitialization(TestConbusDatapointService):
    """Test service initialization and configuration loading"""

    def test_default_initialization(self, tmp_path):
        """Test service initialization with default config"""
        # Use a non-existent config file to test defaults
        non_existent_config = str(tmp_path / "non_existent.yml")
        service = ConbusDatapointService(config_path=non_existent_config)

        assert service.config.ip == "192.168.1.100"
        assert service.config.port == 10001
        assert service.config.timeout == 10
        assert service.is_connected is False
        assert service.socket is None

    def test_config_file_loading(self, service):
        """Test loading configuration from file"""
        assert service.config.ip == "10.0.0.1"
        assert service.config.port == 8080
        assert service.config.timeout == 15

    def test_nonexistent_config_file(self):
        """Test handling of non-existent config file"""
        service = ConbusDatapointService(config_path="nonexistent.yml")

        # Should use defaults when config file doesn't exist
        assert service.config.ip == "192.168.1.100"
        assert service.config.port == 10001
        assert service.config.timeout == 10

    @patch("yaml.safe_load")
    @patch("builtins.open")
    @patch("os.path.exists", return_value=True)
    def test_config_file_error_handling(self, mock_exists, mock_open, mock_yaml):
        """Test error handling when config file is malformed"""
        mock_yaml.side_effect = Exception("YAML parsing error")

        service = ConbusDatapointService(config_path="bad_config.yml")

        # Should use defaults when config parsing fails
        assert service.config.ip == "192.168.1.100"
        assert service.config.port == 10001
        assert service.config.timeout == 10


class TestConnectionManagement(TestConbusDatapointService):
    """Test connection establishment and management"""

    @patch("socket.socket")
    def test_successful_connection(self, mock_socket_class, service, mock_socket):
        """Test successful connection establishment"""
        mock_socket_class.return_value = mock_socket

        result = service.connect()

        assert result.success is True
        assert service.is_connected is True
        assert service.socket == mock_socket
        mock_socket.settimeout.assert_called_with(15)  # Service timeout
        mock_socket.connect.assert_called_with(("10.0.0.1", 8080))

    @patch("socket.socket")
    def test_connection_timeout(self, mock_socket_class, service, mock_socket):
        """Test connection timeout handling"""
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.side_effect = socket.timeout()

        result = service.connect()

        assert result.success is False
        assert "Connection timeout after 15 seconds" in result.error
        assert service.is_connected is False

    @patch("socket.socket")
    def test_connection_error(self, mock_socket_class, service, mock_socket):
        """Test connection error handling"""
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.side_effect = ConnectionRefusedError("Connection refused")

        result = service.connect()

        assert result.success is False
        assert "Failed to connect to 10.0.0.1:8080" in result.error
        assert service.is_connected is False

    def test_already_connected(self, service):
        """Test connecting when already connected"""
        service.is_connected = True

        result = service.connect()

        assert result.success is True
        assert "Already connected" in result.data["message"]

    def test_disconnect(self, service, mock_socket):
        """Test disconnection"""
        service.socket = mock_socket
        service.is_connected = True

        service.disconnect()

        assert service.is_connected is False
        assert service.socket is None
        mock_socket.close.assert_called_once()

    def test_disconnect_with_error(self, service, mock_socket):
        """Test disconnection with socket error"""
        service.socket = mock_socket
        service.is_connected = True
        mock_socket.close.side_effect = Exception("Close error")

        service.disconnect()  # Should not raise exception

        assert service.is_connected is False
        assert service.socket is None


class TestTelegramGeneration(TestConbusDatapointService):
    """Test telegram generation for different types"""

    def test_version_telegram_without_serial(self, service):
        """Test version telegram generation without target serial"""
        request = ConbusDatapointRequest(datapoint_type=DatapointTypeName.VERSION)

        telegram = service._generate_telegram(request)

        assert telegram is None

    def test_sensor_telegram_without_serial(self, service):
        """Test sensor telegram generation without target serial"""
        request = ConbusDatapointRequest(datapoint_type=DatapointTypeName.VOLTAGE)

        # Should return None instead of raising exception in _generate_telegram
        telegram = service._generate_telegram(request)
        assert telegram is None

class TestConvenienceMethods(TestConbusDatapointService):
    """Test convenience methods"""

    @patch.object(ConbusDatapointService, "send_telegram")
    def test_send_version_request(self, mock_send, service):
        """Test send_version_request convenience method"""
        mock_response = ConbusDatapointResponse(
            success=True,
            request=ConbusDatapointRequest(
                datapoint_type=DatapointTypeName.VERSION,
                target_serial="0020030837"
            ),
            sent_telegram="<S0020030837F02D02FM>",
        )
        mock_send.return_value = mock_response

        response = service.send_version_request("0020030837")

        assert response.success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        assert args.datapoint_type.value == DatapointTypeName.VERSION.value
        assert args.target_serial == "0020030837"

    @patch.object(ConbusDatapointService, "send_telegram")
    def test_send_sensor_request(self, mock_send, service):
        """Test send_sensor_request convenience method"""
        mock_response = ConbusDatapointResponse(
            success=True,
            request=ConbusDatapointRequest(
                datapoint_type=DatapointTypeName.TEMPERATURE, target_serial="0020012521"
            ),
            sent_telegram="<S0020012521F02D18FM>",
        )
        mock_send.return_value = mock_response

        response = service.datapoint_request("0020012521", DatapointTypeName.TEMPERATURE)

        assert response.success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        assert args.datapoint_type == DatapointTypeName.TEMPERATURE
        assert args.target_serial == "0020012521"

    def test_send_sensor_request_invalid_type(self, service):
        """Test send_sensor_request with invalid sensor type"""
        with pytest.raises(ConbusDatapointError, match="Invalid sensor type"):
            service.datapoint_request("0020030837", DatapointTypeName.UNKNOWN)


class TestCustomTelegrams(TestConbusDatapointService):
    """Test custom telegram functionality"""

    @patch("socket.socket")
    def test_send_custom_telegram(self, mock_socket_class, service, mock_socket):
        """Test sending custom telegram"""
        mock_socket_class.return_value = mock_socket
        mock_socket.recv.side_effect = [b"<R0020030837F02DE2COUCOUFM>", b""]

        response = service.send_custom_telegram("0020030837", "02", "E2")

        assert response.success is True
        # Verify telegram structure
        sent_telegram = response.sent_telegram
        assert sent_telegram.startswith("<S0020030837F02DE2")
        assert sent_telegram.endswith(">")
        assert response.received_telegrams[0] == "<R0020030837F02DE2COUCOUFM>"


class TestConnectionStatus(TestConbusDatapointService):
    """Test connection status functionality"""

    def test_get_connection_status_disconnected(self, service):
        """Test getting status when disconnected"""
        status = service.get_connection_status()

        assert status.connected is False
        assert status.ip == "10.0.0.1"
        assert status.port == 8080
        assert status.last_activity is None

    def test_get_connection_status_connected(self, service):
        """Test getting status when connected"""
        service.is_connected = True
        service.last_activity = datetime(2023, 8, 27, 14, 30, 0)

        status = service.get_connection_status()

        assert status.connected is True
        assert status.ip == "10.0.0.1"
        assert status.port == 8080
        assert status.last_activity == datetime(2023, 8, 27, 14, 30, 0)


class TestContextManager(TestConbusDatapointService):
    """Test context manager functionality"""

    def test_context_manager_enter_exit(self, service, mock_socket):
        """Test context manager enter and exit"""
        service.socket = mock_socket
        service.is_connected = True

        with service as ctx_service:
            assert ctx_service == service

        # Should disconnect on exit
        assert service.is_connected is False
        mock_socket.close.assert_called_once()


class TestErrorHandling(TestConbusDatapointService):
    """Test error handling scenarios"""

    def test_response_receiving_error(self, service, mock_socket):
        """Test error handling during response receiving"""
        service.socket = mock_socket
        service.is_connected = True
        mock_socket.recv.side_effect = Exception("Network error")

        responses = service._receive_responses()

        assert responses == []

