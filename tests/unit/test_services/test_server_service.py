"""Tests for ServerService."""

from unittest.mock import Mock, patch
import pytest

from xp.services.server_service import ServerService, ServerError


class TestServerError:
    """Test ServerError exception."""

    def test_server_error_is_exception(self):
        """Test ServerError inherits from Exception."""
        assert issubclass(ServerError, Exception)

    def test_server_error_can_be_raised(self):
        """Test ServerError can be raised."""
        with pytest.raises(ServerError):
            raise ServerError("Server failed")

    def test_server_error_with_message(self):
        """Test ServerError with custom message."""
        msg = "Server initialization failed"
        with pytest.raises(ServerError) as exc_info:
            raise ServerError(msg)
        assert str(exc_info.value) == msg


class TestServerServiceInit:
    """Test ServerService initialization."""

    @patch("xp.services.server_service.Path")
    def test_init_with_defaults(self, mock_path):
        """Test initialization with default parameters."""
        mock_path.return_value.exists.return_value = False

        service = ServerService()

        assert service.config_path == "server.yml"
        assert service.port == 10001
        assert service.is_running is False
        assert service.server_socket is None
        assert service.devices == []
        assert service.device_services == {}

    @patch("xp.services.server_service.Path")
    def test_init_with_custom_params(self, mock_path):
        """Test initialization with custom parameters."""
        mock_path.return_value.exists.return_value = False

        service = ServerService(config_path="custom.yml", port=8080)

        assert service.config_path == "custom.yml"
        assert service.port == 8080

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_init_loads_config_when_exists(self, mock_config, mock_path):
        """Test initialization loads config when file exists."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock()
        mock_module.enabled = True
        mock_module.serial_number = "12345"
        mock_module.module_type = "XP33"
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert len(service.devices) == 1
        mock_config.from_yaml.assert_called_once_with("server.yml")


class TestServerServiceConfig:
    """Test ServerService configuration methods."""

    @patch("xp.services.server_service.Path")
    def test_load_device_config_file_not_found(self, mock_path):
        """Test loading config when file doesn't exist."""
        mock_path.return_value.exists.return_value = False

        service = ServerService()

        assert service.devices == []
        assert service.device_services == {}

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_load_device_config_with_disabled_devices(self, mock_config, mock_path):
        """Test loading config filters out disabled devices."""
        mock_path.return_value.exists.return_value = True
        mock_enabled = Mock(enabled=True, serial_number="11111", module_type="XP33")
        mock_disabled = Mock(enabled=False, serial_number="22222", module_type="XP33")
        mock_config.from_yaml.return_value = Mock(root=[mock_enabled, mock_disabled])

        service = ServerService()

        assert len(service.devices) == 1
        assert service.devices[0].serial_number == "11111"

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_load_device_config_handles_exception(self, mock_config, mock_path):
        """Test loading config handles exceptions gracefully."""
        mock_path.return_value.exists.return_value = True
        mock_config.from_yaml.side_effect = Exception("Parse error")

        service = ServerService()

        assert service.devices == []
        assert service.device_services == {}

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_device_services_xp33(self, mock_config, mock_path):
        """Test creating XP33 device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="12345", module_type="XP33")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "12345" in service.device_services

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_device_services_cp20(self, mock_config, mock_path):
        """Test creating CP20 device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="11111", module_type="CP20")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "11111" in service.device_services

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_device_services_xp20(self, mock_config, mock_path):
        """Test creating XP20 device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="22222", module_type="XP20")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "22222" in service.device_services

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_device_services_unknown_type(self, mock_config, mock_path):
        """Test creating device service with unknown type."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="99999", module_type="UNKNOWN")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "99999" not in service.device_services


class TestServerServiceLifecycle:
    """Test ServerService start/stop methods."""

    @patch("xp.services.server_service.Path")
    def test_start_server_when_already_running(self, mock_path):
        """Test starting server when already running raises error."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        service.is_running = True

        with pytest.raises(ServerError, match="already running"):
            service.start_server()

    @patch("xp.services.server_service.Path")
    def test_stop_server_when_not_running(self, mock_path):
        """Test stopping server when not running does nothing."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        service.is_running = False

        service.stop_server()  # Should not raise

    @patch("xp.services.server_service.Path")
    def test_stop_server_closes_socket(self, mock_path):
        """Test stopping server closes socket."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        service.is_running = True
        service.server_socket = Mock()

        service.stop_server()

        service.server_socket.close.assert_called_once()
        assert service.is_running is False

    @patch("xp.services.server_service.Path")
    def test_stop_server_handles_close_exception(self, mock_path):
        """Test stopping server handles socket close exceptions."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        service.is_running = True
        service.server_socket = Mock()
        service.server_socket.close.side_effect = Exception("Close failed")

        service.stop_server()  # Should not raise

        assert service.is_running is False


class TestServerServiceStatus:
    """Test ServerService status methods."""

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_get_server_status(self, mock_config, mock_path):
        """Test getting server status."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="12345", module_type="XP33")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService(port=8080)
        service.is_running = True

        status = service.get_server_status()

        assert status["running"] is True
        assert status["port"] == 8080
        assert status["devices_configured"] == 1
        assert "12345" in status["device_list"]

    @patch("xp.services.server_service.Path")
    def test_get_server_status_not_running(self, mock_path):
        """Test getting server status when not running."""
        mock_path.return_value.exists.return_value = False
        status = ServerService().get_server_status()

        assert status["running"] is False
        assert status["devices_configured"] == 0
        assert status["device_list"] == []


class TestServerServiceRequestProcessing:
    """Test ServerService request processing."""

    @patch("xp.services.server_service.Path")
    def test_process_request_invalid_telegram(self, mock_path):
        """Test processing invalid telegram returns empty list."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        service.telegram_service = Mock()
        service.telegram_service.parse_system_telegram.return_value = None

        responses = service._process_request("<INVALID>")

        assert responses == []

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_process_request_discover(self, mock_config, mock_path):
        """Test processing discover request."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="12345", module_type="XP33")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()
        mock_telegram = Mock()
        service.telegram_service.parse_system_telegram = Mock(
            return_value=mock_telegram
        )
        service.discover_service.is_discover_request = Mock(return_value=True)
        service.device_services["12345"].generate_discover_response = Mock(
            return_value="<DISCOVER_RESPONSE>"
        )

        responses = service._process_request("<S0000000000F01D>")

        assert len(responses) == 1
        assert "<DISCOVER_RESPONSE>" in responses[0]

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_process_request_specific_device(self, mock_config, mock_path):
        """Test processing request for specific device."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="12345", module_type="XP33")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()
        mock_telegram = Mock(serial_number="12345")
        service.telegram_service.parse_system_telegram = Mock(
            return_value=mock_telegram
        )
        service.discover_service.is_discover_request = Mock(return_value=False)
        service.device_services["12345"].process_system_telegram = Mock(
            return_value="<RESPONSE>"
        )

        responses = service._process_request("<S0000012345F02D>")

        assert len(responses) == 1
        assert "<RESPONSE>" in responses[0]

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_process_request_broadcast(self, mock_config, mock_path):
        """Test processing broadcast request."""
        mock_path.return_value.exists.return_value = True
        mock_module1 = Mock(enabled=True, serial_number="11111", module_type="XP33")
        mock_module2 = Mock(enabled=True, serial_number="22222", module_type="XP20")
        mock_config.from_yaml.return_value = Mock(root=[mock_module1, mock_module2])

        service = ServerService()
        mock_telegram = Mock(serial_number="0000000000")
        service.telegram_service.parse_system_telegram = Mock(
            return_value=mock_telegram
        )
        service.discover_service.is_discover_request = Mock(return_value=False)
        service.device_services["11111"].process_system_telegram = Mock(
            return_value="<RESPONSE1>"
        )
        service.device_services["22222"].process_system_telegram = Mock(
            return_value="<RESPONSE2>"
        )

        responses = service._process_request("<S0000000000F02D>")

        assert len(responses) == 2

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_process_request_broadcast_with_none_response(self, mock_config, mock_path):
        """Test processing broadcast request where some devices return None."""
        mock_path.return_value.exists.return_value = True
        mock_module1 = Mock(enabled=True, serial_number="11111", module_type="XP33")
        mock_module2 = Mock(enabled=True, serial_number="22222", module_type="XP20")
        mock_config.from_yaml.return_value = Mock(root=[mock_module1, mock_module2])

        service = ServerService()
        mock_telegram = Mock(serial_number="0000000000")
        service.telegram_service.parse_system_telegram = Mock(
            return_value=mock_telegram
        )
        service.discover_service.is_discover_request = Mock(return_value=False)
        service.device_services["11111"].process_system_telegram = Mock(
            return_value="<RESPONSE1>"
        )
        service.device_services["22222"].process_system_telegram = Mock(
            return_value=None  # This device returns None
        )

        responses = service._process_request("<S0000000000F02D>")

        assert len(responses) == 1  # Only one response
        assert "<RESPONSE1>" in responses[0]

    @patch("xp.services.server_service.Path")
    def test_process_request_device_not_found(self, mock_path):
        """Test processing request for non-existent device."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        mock_telegram = Mock(serial_number="99999")
        service.telegram_service.parse_system_telegram = Mock(
            return_value=mock_telegram
        )
        service.discover_service.is_discover_request = Mock(return_value=False)

        responses = service._process_request("<S0000099999F02D>")

        assert responses == []

    @patch("xp.services.server_service.Path")
    def test_process_request_handles_exception(self, mock_path):
        """Test processing request handles exceptions."""
        mock_path.return_value.exists.return_value = False
        service = ServerService()
        mock_telegram_service = Mock()
        mock_telegram_service.parse_system_telegram.side_effect = Exception(
            "Parse error"
        )
        service.telegram_service = mock_telegram_service

        responses = service._process_request("<INVALID>")

        assert responses == []


class TestServerServiceReload:
    """Test ServerService config reload."""

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_reload_config(self, mock_config, mock_path):
        """Test reloading configuration."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="12345", module_type="XP33")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        # Change config
        mock_module2 = Mock(enabled=True, serial_number="22222", module_type="XP20")
        mock_config.from_yaml.return_value = Mock(root=[mock_module, mock_module2])

        service.reload_config()

        assert len(service.devices) == 2


class TestServerServiceDeviceTypes:
    """Test device type creation."""

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_xp24_service(self, mock_config, mock_path):
        """Test creating XP24 device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="24242", module_type="XP24")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "24242" in service.device_services

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_xp33led_service(self, mock_config, mock_path):
        """Test creating XP33LED device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="33333", module_type="XP33LED")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "33333" in service.device_services

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_xp130_service(self, mock_config, mock_path):
        """Test creating XP130 device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="13013", module_type="XP130")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "13013" in service.device_services

    @patch("xp.services.server_service.Path")
    @patch("xp.services.server_service.ConsonModuleListConfig")
    def test_create_xp230_service(self, mock_config, mock_path):
        """Test creating XP230 device service."""
        mock_path.return_value.exists.return_value = True
        mock_module = Mock(enabled=True, serial_number="23023", module_type="XP230")
        mock_config.from_yaml.return_value = Mock(root=[mock_module])

        service = ServerService()

        assert "23023" in service.device_services
