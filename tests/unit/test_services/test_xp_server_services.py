"""Tests for XP device server services."""

from unittest.mock import Mock

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.services.server.cp20_server_service import CP20ServerService
from xp.services.server.xp20_server_service import XP20ServerService
from xp.services.server.xp33_server_service import XP33ServerService
from xp.services.server.xp130_server_service import XP130ServerService
from xp.services.server.xp230_server_service import XP230ServerService


class TestXP33ServerService:
    """Test XP33ServerService."""

    def test_init_default_variant(self):
        """Test initialization with default variant."""
        service = XP33ServerService("12345")

        assert service.serial_number == "12345"
        assert service.variant == "XP33LR"
        assert service.device_type == "XP33"

    def test_init_xp33_variant(self):
        """Test initialization with XP33 variant."""
        service = XP33ServerService("12345", "XP33")

        assert service.variant == "XP33"
        assert service.module_type_code.value == 11
        assert "XP33_V" in service.firmware_version

    def test_init_xp33lr_variant(self):
        """Test initialization with XP33LR variant."""
        service = XP33ServerService("12345", "XP33LR")

        assert service.variant == "XP33LR"
        assert service.module_type_code.value == 30
        assert "XP33LR_V" in service.firmware_version

    def test_init_xp33led_variant(self):
        """Test initialization with XP33LED variant."""
        service = XP33ServerService("12345", "XP33LED")

        assert service.variant == "XP33LED"
        assert service.module_type_code.value == 35
        assert "XP33LED_V" in service.firmware_version

    def test_generate_discover_response(self):
        """Test discover response generation."""
        response = XP33ServerService("12345").generate_discover_response()

        assert "<R12345F01D" in response
        assert response.endswith(">")


class TestXP20ServerService:
    """Test XP20ServerService."""

    def test_init(self):
        """Test initialization."""
        service = XP20ServerService("11111")

        assert service.serial_number == "11111"
        assert service.device_type == "XP20"
        assert service.module_type_code.value == 33

    def test_generate_discover_response(self):
        """Test discover response generation."""
        response = XP20ServerService("11111").generate_discover_response()

        assert "<R11111F01D" in response
        assert response.endswith(">")


class TestXP130ServerService:
    """Test XP130ServerService."""

    def test_init(self):
        """Test initialization."""
        service = XP130ServerService("22222")

        assert service.serial_number == "22222"
        assert service.device_type == "XP130"
        assert service.module_type_code.value == 13

    def test_generate_discover_response(self):
        """Test discover response generation."""
        response = XP130ServerService("22222").generate_discover_response()

        assert "<R22222F01D" in response
        assert response.endswith(">")


class TestXP230ServerService:
    """Test XP230ServerService."""

    def test_init(self):
        """Test initialization."""
        service = XP230ServerService("33333")

        assert service.serial_number == "33333"
        assert service.device_type == "XP230"
        assert service.module_type_code.value == 34

    def test_generate_discover_response(self):
        """Test discover response generation."""
        response = XP230ServerService("33333").generate_discover_response()

        assert "<R33333F01D" in response
        assert response.endswith(">")


class TestCP20ServerService:
    """Test CP20ServerService."""

    def test_init(self):
        """Test initialization."""
        service = CP20ServerService("44444")

        assert service.serial_number == "44444"
        assert service.device_type == "CP20"
        assert service.module_type_code.value == 2

    def test_generate_discover_response(self):
        """Test discover response generation."""
        response = CP20ServerService("44444").generate_discover_response()

        assert "<R44444F01D" in response
        assert response.endswith(">")

    def test_get_device_info(self):
        """Test getting device info."""
        info = CP20ServerService("44444").get_device_info()

        assert info["serial_number"] == "44444"
        assert info["device_type"] == "CP20"
        assert info["firmware_version"] == "CP20_V0.01.05"

    def test_handle_device_specific_data_request(self):
        """Test device-specific data request handling."""
        service = CP20ServerService("44444")
        request = Mock()

        response = service._handle_device_specific_data_request(request)

        assert response is None


class TestXP130ServerServiceExtended:
    """Additional XP130ServerService tests."""

    def test_network_configuration(self):
        """Test XP130 network configuration."""
        service = XP130ServerService("22222")

        assert service.ip_address == "192.168.1.100"
        assert service.subnet_mask == "255.255.255.0"
        assert service.gateway == "192.168.1.1"

    def test_get_device_info(self):
        """Test getting device info."""
        info = XP130ServerService("22222").get_device_info()

        assert info["serial_number"] == "22222"
        assert info["device_type"] == "XP130"
        assert info["ip_address"] == "192.168.1.100"


class TestXP230ServerServiceExtended:
    """Additional XP230ServerService tests."""

    def test_get_device_info(self):
        """Test getting device info."""
        info = XP230ServerService("33333").get_device_info()

        assert info["serial_number"] == "33333"
        assert info["device_type"] == "XP230"
        assert info["firmware_version"] == "XP230_V1.00.04"


class TestXP20ServerServiceExtended:
    """Additional XP20ServerService tests."""

    def test_get_device_info(self):
        """Test getting device info."""
        info = XP20ServerService("11111").get_device_info()

        assert info["serial_number"] == "11111"
        assert info["device_type"] == "XP20"
        assert info["firmware_version"] == "XP20_V0.01.05"


class TestXP33StormModeSimulator:
    """Test XP33 Storm Mode Simulator functionality."""

    def test_storm_mode_initialization(self):
        """Test storm mode is initialized to False."""
        service = XP33ServerService("0012345003")

        assert service.storm_mode is False
        assert service.last_response is None

    def test_trigger_storm_mode_d99(self):
        """Test D99 query triggers storm mode."""
        service = XP33ServerService("0012345003")

        # Set up prerequisites: cached response
        service.last_response = "<R0012345003F02D1503000[%],01:050[%],02:100[%]FX>\n"

        # Create D99 trigger request using Mock
        request = Mock()
        request.serial_number = "0012345003"
        request.system_function = SystemFunction.READ_DATAPOINT
        request.datapoint_type = None
        request.data = "99"

        response = service._handle_device_specific_data_request(request)

        assert service.storm_mode is True
        assert service.storm_thread is not None
        assert service.storm_thread.is_alive()
        assert response is None  # No response when entering storm mode

    def test_normal_error_code_query(self):
        """Test MODULE_ERROR_CODE query returns 00 in normal state."""
        service = XP33ServerService("0012345003")

        request = Mock()
        request.serial_number = "0012345003"
        request.system_function = SystemFunction.READ_DATAPOINT
        request.datapoint_type = DataPointType.MODULE_ERROR_CODE
        request.data = "10"

        response = service._handle_device_specific_data_request(request)

        assert service.storm_mode is False
        assert response is not None
        assert "D10" in response
        assert "00" in response  # Error code 00 = normal

    def test_exit_storm_mode_with_error_code_query(self):
        """Test MODULE_ERROR_CODE query stops storm and returns FE."""
        service = XP33ServerService("0012345003")

        # First trigger storm mode
        service.storm_mode = True

        # Send MODULE_ERROR_CODE query
        request = Mock()
        request.serial_number = "0012345003"
        request.system_function = SystemFunction.READ_DATAPOINT
        request.datapoint_type = DataPointType.MODULE_ERROR_CODE
        request.data = "10"

        response = service._handle_device_specific_data_request(request)

        assert service.storm_mode is False
        assert response is not None
        assert "D10" in response
        assert "FE" in response  # Error code FE = buffer overflow

    def test_storm_mode_ignores_queries(self):
        """Test storm mode ignores queries (background thread is sending)."""
        service = XP33ServerService("0012345003")

        # Set up storm mode
        service.last_response = "<R0012345003F02D1503000[%],01:050[%],02:100[%]FX>\n"
        service.storm_mode = True

        # Query a normal datapoint during storm
        request = Mock()
        request.serial_number = "0012345003"
        request.system_function = SystemFunction.READ_DATAPOINT
        request.datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        request.data = "15"

        response = service._handle_device_specific_data_request(request)

        # Should return None (ignoring query, background thread is sending)
        assert response is None

    def test_storm_without_cached_response(self):
        """Test storm mode trigger without cached response."""
        service = XP33ServerService("0012345003")
        service.last_response = None  # No cached response

        # Trigger storm mode
        request = Mock()
        request.datapoint_type = None
        request.data = "99"

        response = service._trigger_storm_mode()

        # Should not start storm without cached response
        assert response is None
        assert service.storm_mode is False  # Storm not activated

    def test_full_storm_sequence(self):
        """Test complete storm mode sequence: trigger -> storm -> recovery -> normal."""
        service = XP33ServerService("0012345003")

        # Step 1: Query normal datapoint to cache a response
        request_light = Mock()
        request_light.serial_number = "0012345003"
        request_light.system_function = SystemFunction.READ_DATAPOINT
        request_light.datapoint_type = DataPointType.MODULE_LIGHT_LEVEL
        request_light.data = "15"

        service._handle_device_specific_data_request(request_light)
        assert service.last_response is not None

        # Step 2: Trigger storm with D99
        request_trigger = Mock()
        request_trigger.serial_number = "0012345003"
        request_trigger.system_function = SystemFunction.READ_DATAPOINT
        request_trigger.datapoint_type = None
        request_trigger.data = "99"

        trigger_response = service._handle_device_specific_data_request(request_trigger)
        assert trigger_response is None
        assert service.storm_mode is True
        assert service.storm_thread is not None
        assert service.storm_thread.is_alive()

        # Step 3: Query during storm should be ignored (background thread sending)
        storm_response = service._handle_device_specific_data_request(request_light)
        assert storm_response is None  # Ignored during storm

        # Step 4: MODULE_ERROR_CODE query stops storm
        request_error = Mock()
        request_error.serial_number = "0012345003"
        request_error.system_function = SystemFunction.READ_DATAPOINT
        request_error.datapoint_type = DataPointType.MODULE_ERROR_CODE
        request_error.data = "10"

        recovery_response = service._handle_device_specific_data_request(request_error)
        assert recovery_response is not None
        assert service.storm_mode is False
        assert "FE" in recovery_response  # type: ignore[unreachable]

        # Step 5: Verify normal operation resumed
        normal_again = service._handle_device_specific_data_request(request_error)
        assert "00" in normal_again  # Normal error code

    def test_build_error_code_response(self):
        """Test error code response builder."""
        service = XP33ServerService("0012345003")

        # Test normal error code
        response_normal = service._build_error_code_response("00")
        assert "R0012345003" in response_normal
        assert "D10" in response_normal
        assert "00" in response_normal

        # Test buffer overflow error code
        response_error = service._build_error_code_response("FE")
        assert "R0012345003" in response_error
        assert "D10" in response_error
        assert "FE" in response_error
