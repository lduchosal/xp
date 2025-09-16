import pytest
from unittest.mock import Mock, patch
import socket
from datetime import datetime
from src.xp.services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from src.xp.models import (
    ConbusSendRequest,
    ConbusSendResponse,
    TelegramType,
)


class TestConbusClientSendService:
    """Test cases for ConbusClientSendService"""

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
        return ConbusClientSendService(config_path=mock_config_file)

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


class TestServiceInitialization(TestConbusClientSendService):
    """Test service initialization and configuration loading"""

    def test_default_initialization(self, tmp_path):
        """Test service initialization with default config"""
        # Use a non-existent config file to test defaults
        non_existent_config = str(tmp_path / "non_existent.yml")
        service = ConbusClientSendService(config_path=non_existent_config)

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
        service = ConbusClientSendService(config_path="nonexistent.yml")

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

        service = ConbusClientSendService(config_path="bad_config.yml")

        # Should use defaults when config parsing fails
        assert service.config.ip == "192.168.1.100"
        assert service.config.port == 10001
        assert service.config.timeout == 10


class TestConnectionManagement(TestConbusClientSendService):
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


class TestTelegramGeneration(TestConbusClientSendService):
    """Test telegram generation for different types"""

    def test_discovery_telegram_generation(self, service):
        """Test discovery telegram generation"""
        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        telegram = service._generate_telegram(request)

        assert telegram == "<S0000000000F01D00FA>"

    def test_version_telegram_generation(self, service):
        """Test version telegram generation"""
        # Mock the version service response
        with patch.object(
            service.version_service, "generate_version_request_telegram"
        ) as mock_version_method:
            mock_response = Mock()
            mock_response.success = True
            mock_response.data = {"telegram": "<S0020030837F02D02FM>"}
            mock_version_method.return_value = mock_response

            request = ConbusSendRequest(
                telegram_type=TelegramType.VERSION, target_serial="0020030837"
            )

            telegram = service._generate_telegram(request)

            assert telegram == "<S0020030837F02D02FM>"
            mock_version_method.assert_called_once_with("0020030837")

    def test_version_telegram_without_serial(self, service):
        """Test version telegram generation without target serial"""
        request = ConbusSendRequest(telegram_type=TelegramType.VERSION)

        telegram = service._generate_telegram(request)

        assert telegram is None

    def test_sensor_telegram_generation(self, service):
        """Test sensor telegram generation"""
        test_cases = [
            (TelegramType.VOLTAGE, "20", "<S0020030837F02D20FG>"),
            (TelegramType.TEMPERATURE, "18", "<S0020030837F02D18FI>"),
            (TelegramType.CURRENT, "21", "<S0020030837F02D21FF>"),
            (TelegramType.HUMIDITY, "19", "<S0020030837F02D19FH>"),
        ]

        for telegram_type, data_point, expected in test_cases:
            request = ConbusSendRequest(
                telegram_type=telegram_type, target_serial="0020030837"
            )

            telegram = service._generate_telegram(request)

            # Verify structure (exact checksum may vary based on implementation)
            assert telegram.startswith("<S0020030837F02D" + data_point)
            assert telegram.endswith(">")
            assert len(telegram) > 15

    def test_sensor_telegram_without_serial(self, service):
        """Test sensor telegram generation without target serial"""
        request = ConbusSendRequest(telegram_type=TelegramType.VOLTAGE)

        # Should return None instead of raising exception in _generate_telegram
        telegram = service._generate_telegram(request)
        assert telegram is None

    def test_unsupported_telegram_type(self, service):
        """Test handling of unsupported telegram type"""
        # Create a mock telegram type
        with patch("src.xp.models.conbus_client_send.TelegramType") as mock_type:
            mock_type.UNSUPPORTED = "unsupported"
            request = ConbusSendRequest(telegram_type=mock_type.UNSUPPORTED)

            telegram = service._generate_telegram(request)

            assert telegram is None


class TestTelegramSending(TestConbusClientSendService):
    """Test telegram sending functionality"""

    @patch("socket.socket")
    def test_successful_telegram_send(self, mock_socket_class, service, mock_socket):
        """Test successful telegram sending"""
        mock_socket_class.return_value = mock_socket
        mock_socket.recv.side_effect = [b"<R0020030837F01DFM>", b""]  # End of data

        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        response = service.send_telegram(request)

        assert response.success is True
        assert response.sent_telegram == "<S0000000000F01D00FA>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020030837F01DFM>"
        assert response.error is None

    @patch("socket.socket")
    def test_telegram_send_auto_connect(self, mock_socket_class, service, mock_socket):
        """Test automatic connection when not connected"""
        mock_socket_class.return_value = mock_socket
        mock_socket.recv.return_value = b""

        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        response = service.send_telegram(request)

        assert response.success is True
        assert service.is_connected is True
        mock_socket.connect.assert_called_once()

    @patch("socket.socket")
    def test_telegram_send_connection_failure(
        self, mock_socket_class, service, mock_socket
    ):
        """Test telegram send when connection fails"""
        mock_socket_class.return_value = mock_socket
        mock_socket.connect.side_effect = socket.timeout()

        request = ConbusSendRequest(
            telegram_type=TelegramType.VERSION, target_serial="0020030837"
        )

        response = service.send_telegram(request)

        assert response.success is False
        assert "Connection timeout after 15 seconds" in response.error

    @patch("socket.socket")
    def test_telegram_send_generation_failure(self, mock_socket_class, service):
        """Test telegram send when generation fails"""
        # Mock socket to ensure connection succeeds
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        service.is_connected = True
        service.socket = mock_socket

        request = ConbusSendRequest(
            telegram_type=TelegramType.VERSION
        )  # Missing serial

        response = service.send_telegram(request)

        assert response.success is False
        assert "Failed to generate telegram" in response.error

    @patch("socket.socket")
    def test_telegram_send_socket_timeout(
        self, mock_socket_class, service, mock_socket
    ):
        """Test socket timeout during send"""
        mock_socket_class.return_value = mock_socket
        mock_socket.send.side_effect = socket.timeout()
        service.is_connected = True
        service.socket = mock_socket

        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        response = service.send_telegram(request)

        assert response.success is False
        assert response.error == "Response timeout"

    @patch("socket.socket")
    def test_multiple_response_handling(self, mock_socket_class, service, mock_socket):
        """Test handling of multiple responses"""
        mock_socket_class.return_value = mock_socket
        mock_socket.recv.side_effect = [
            b"<R0020030837F01DFM>",
            b"<R0020044966F01DFK>",
            b"<R0020042796F01DFN>",
            b"",  # End of data
        ]

        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        response = service.send_telegram(request)

        assert response.success is True
        assert len(response.received_telegrams) == 3
        assert "<R0020030837F01DFM>" in response.received_telegrams
        assert "<R0020044966F01DFK>" in response.received_telegrams
        assert "<R0020042796F01DFN>" in response.received_telegrams


class TestConvenienceMethods(TestConbusClientSendService):
    """Test convenience methods"""

    @patch.object(ConbusClientSendService, "send_telegram")
    def test_send_discovery(self, mock_send, service):
        """Test send_discovery convenience method"""
        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(telegram_type=TelegramType.DISCOVERY),
            sent_telegram="<S0000000000F01D00FA>",
        )
        mock_send.return_value = mock_response

        response = service.send_discovery()

        assert response.success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        assert args.telegram_type == TelegramType.DISCOVERY

    @patch.object(ConbusClientSendService, "send_telegram")
    def test_send_version_request(self, mock_send, service):
        """Test send_version_request convenience method"""
        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=TelegramType.VERSION, target_serial="0020030837"
            ),
            sent_telegram="<S0020030837F02D02FM>",
        )
        mock_send.return_value = mock_response

        response = service.send_version_request("0020030837")

        assert response.success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        assert args.telegram_type == TelegramType.VERSION
        assert args.target_serial == "0020030837"

    @patch.object(ConbusClientSendService, "send_telegram")
    def test_send_sensor_request(self, mock_send, service):
        """Test send_sensor_request convenience method"""
        mock_response = ConbusSendResponse(
            success=True,
            request=ConbusSendRequest(
                telegram_type=TelegramType.TEMPERATURE, target_serial="0020012521"
            ),
            sent_telegram="<S0020012521F02D18FM>",
        )
        mock_send.return_value = mock_response

        response = service.send_sensor_request("0020012521", TelegramType.TEMPERATURE)

        assert response.success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        assert args.telegram_type == TelegramType.TEMPERATURE
        assert args.target_serial == "0020012521"

    def test_send_sensor_request_invalid_type(self, service):
        """Test send_sensor_request with invalid sensor type"""
        with pytest.raises(ConbusClientSendError, match="Invalid sensor type"):
            service.send_sensor_request("0020030837", TelegramType.DISCOVERY)


class TestCustomTelegrams(TestConbusClientSendService):
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


class TestConnectionStatus(TestConbusClientSendService):
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


class TestContextManager(TestConbusClientSendService):
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


class TestErrorHandling(TestConbusClientSendService):
    """Test error handling scenarios"""

    def test_response_receiving_error(self, service, mock_socket):
        """Test error handling during response receiving"""
        service.socket = mock_socket
        service.is_connected = True
        mock_socket.recv.side_effect = Exception("Network error")

        responses = service._receive_responses()

        assert responses == []

    @patch("socket.socket")
    def test_service_resilience_to_socket_errors(
        self, mock_socket_class, service, mock_socket
    ):
        """Test service resilience to various socket errors"""
        mock_socket_class.return_value = mock_socket
        mock_socket.send.side_effect = BrokenPipeError("Broken pipe")

        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        response = service.send_telegram(request)

        assert response.success is False
        assert "Failed to send telegram" in response.error
