import socket
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

from xp.services.conbus_datapoint_service import (
    ConbusService,
)


class TestConbusService:
    """Test cases for ConbusService"""

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
        return ConbusService(config_path=mock_config_file)

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


class TestServiceInitialization(TestConbusService):
    """Test service initialization and configuration loading"""

    def test_default_initialization(self, tmp_path):
        """Test service initialization with default config"""
        # Use a non-existent config file to test defaults
        non_existent_config = str(tmp_path / "non_existent.yml")
        service = ConbusService(config_path=non_existent_config)

        assert service.config.ip == "192.168.1.100"
        assert service.config.port == 10001
        assert service.config.timeout == 0.1

    def test_nonexistent_config_file(self):
        """Test handling of non-existent config file"""
        service = ConbusService(config_path="nonexistent.yml")

        # Should use defaults when config file doesn't exist
        assert service.config.ip == "192.168.1.100"
        assert service.config.port == 10001
        assert service.config.timeout == 0.1


class TestConnectionManagement(TestConbusService):
    """Test connection establishment and management"""

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_successful_connection(self, mock_pool_class, service):
        """Test successful connection establishment"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        mock_connection = Mock()
        mock_pool_instance.__enter__.return_value = mock_connection
        mock_pool_instance.__exit__.return_value = None

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        result = service.connect()

        assert result.success is True
        assert service.is_connected is True
        mock_pool_instance.__enter__.assert_called_once()
        mock_pool_instance.__exit__.assert_called_once()

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_connection_timeout(self, mock_pool_class, service):
        """Test connection timeout handling"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        mock_pool_instance.__enter__.side_effect = socket.timeout()

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        result = service.connect()

        assert result.success is False
        assert "Failed to establish connection pool" in result.error
        assert service.is_connected is False

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_connection_error(self, mock_pool_class, service):
        """Test connection error handling"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        mock_pool_instance.__enter__.side_effect = ConnectionRefusedError(
            "Connection refused"
        )

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        result = service.connect()

        assert result.success is False
        assert "Failed to establish connection pool to " in result.error
        assert service.is_connected is False

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_already_connected(self, mock_pool_class, service):
        """Test connecting - pool will handle repeated connections gracefully"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        mock_connection = Mock()
        mock_pool_instance.__enter__.return_value = mock_connection
        mock_pool_instance.__exit__.return_value = None

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        result = service.connect()

        assert result.success is True
        assert "Connection pool ready for " in result.data["message"]

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_disconnect(self, mock_pool_class, service):
        """Test disconnection"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        service.is_connected = True

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        service.disconnect()

        assert service.is_connected is False
        mock_pool_instance.close.assert_called_once()

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_disconnect_with_error(self, mock_pool_class, service):
        """Test disconnection with connection pool error"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        service.is_connected = True
        mock_pool_instance.close.side_effect = Exception("Close error")

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        service.disconnect()  # Should not raise exception

        assert service.is_connected is False


class TestConnectionStatus(TestConbusService):
    """Test connection status functionality"""

    def test_get_connection_status_disconnected(self, service):
        """Test getting status when disconnected"""
        status = service.get_connection_status()

        assert status.connected is False
        assert status.last_activity is None

    def test_get_connection_status_connected(self, service):
        """Test getting status when connected"""
        service.is_connected = True
        service.last_activity = datetime(2023, 8, 27, 14, 30, 0)

        status = service.get_connection_status()

        assert status.connected is True
        assert status.last_activity == datetime(2023, 8, 27, 14, 30, 0)


class TestContextManager(TestConbusService):
    """Test context manager functionality"""

    @patch("xp.services.conbus_connection_pool.ConbusConnectionPool")
    def test_context_manager_enter_exit(self, mock_pool_class, service):
        """Test context manager enter and exit"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        service.is_connected = True

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        with service as ctx_service:
            assert ctx_service == service

        # Should disconnect on exit
        assert service.is_connected is False
        mock_pool_instance.close.assert_called_once()


class TestErrorHandling(TestConbusService):
    """Test error handling scenarios"""

    @patch("xp.services.conbus_service.ConbusConnectionPool")
    def test_response_receiving_error(self, mock_pool_class, service, mock_socket):
        """Test error handling during response receiving"""
        mock_pool_instance = MagicMock()
        mock_pool_class.get_instance.return_value = mock_pool_instance
        mock_pool_instance.__enter__.side_effect = Exception("Network error")

        # Replace the service's connection pool with our mock
        service._connection_pool = mock_pool_instance

        responses = service.receive_responses()

        assert responses == []
