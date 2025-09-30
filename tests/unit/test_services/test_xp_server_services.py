"""Tests for XP device server services."""

from unittest.mock import Mock

from xp.services.xp33_server_service import XP33ServerService
from xp.services.xp20_server_service import XP20ServerService
from xp.services.xp130_server_service import XP130ServerService
from xp.services.xp230_server_service import XP230ServerService
from xp.services.cp20_server_service import CP20ServerService


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
        assert service.module_type_code == 11
        assert "XP33_V" in service.firmware_version

    def test_init_xp33lr_variant(self):
        """Test initialization with XP33LR variant."""
        service = XP33ServerService("12345", "XP33LR")

        assert service.variant == "XP33LR"
        assert service.module_type_code == 30
        assert "XP33LR_V" in service.firmware_version

    def test_init_xp33led_variant(self):
        """Test initialization with XP33LED variant."""
        service = XP33ServerService("12345", "XP33LED")

        assert service.variant == "XP33LED"
        assert service.module_type_code == 31
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
        assert service.module_type_code == 33

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
        assert service.module_type_code == 13

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
        assert service.module_type_code == 34

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
        assert service.module_type_code == 2

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
