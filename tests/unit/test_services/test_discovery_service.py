"""Tests for DiscoveryService"""

from unittest.mock import Mock
from src.xp.services.telegram_discovery_service import (
    DiscoveryService,
    DeviceInfo,
)
from src.xp.models.system_telegram import SystemTelegram
from src.xp.models.datapoint_type import DataPointType
from src.xp.models.system_function import SystemFunction
from src.xp.models.reply_telegram import ReplyTelegram


class TestDeviceInfo:
    """Test cases for DeviceInfo class"""

    def test_init(self):
        """Test DeviceInfo initialization"""
        device = DeviceInfo("0020030837")
        assert device.serial_number == "0020030837"
        assert device.checksum_valid is True
        assert device.raw_telegram == ""

    def test_init_with_all_params(self):
        """Test DeviceInfo initialization with all parameters"""
        device = DeviceInfo(
            "0020030837", checksum_valid=False, raw_telegram="<R0020030837F01DFM>"
        )
        assert device.serial_number == "0020030837"
        assert device.checksum_valid is False
        assert device.raw_telegram == "<R0020030837F01DFM>"

    def test_str_representation(self):
        """Test string representation"""
        device_valid = DeviceInfo("0020030837", checksum_valid=True)
        device_invalid = DeviceInfo("0020030837", checksum_valid=False)

        assert str(device_valid) == "Device 0020030837 (✓)"
        assert str(device_invalid) == "Device 0020030837 (✗)"

    def test_repr(self):
        """Test repr representation"""
        device = DeviceInfo("0020030837", checksum_valid=False)
        assert repr(device) == "DeviceInfo(serial='0020030837', checksum_valid=False)"

    def test_to_dict(self):
        """Test dictionary conversion"""
        device = DeviceInfo(
            "0020030837", checksum_valid=True, raw_telegram="<R0020030837F01DFM>"
        )
        result = device.to_dict()

        expected = {
            "serial_number": "0020030837",
            "checksum_valid": True,
            "raw_telegram": "<R0020030837F01DFM>",
        }
        assert result == expected


class TestDiscoveryService:
    """Test cases for DiscoveryService"""

    def test_init(self):
        """Test initialization"""
        service = DiscoveryService()
        assert isinstance(service, DiscoveryService)

    def test_generate_discovery_telegram(self):
        """Test generating discovery broadcast telegram"""
        service = DiscoveryService()

        result = service.generate_discovery_telegram()
        assert result == "<S0000000000F01D00FA>"

    def test_create_discovery_telegram_object(self):
        """Test creating SystemTelegram object for discovery"""
        service = DiscoveryService()

        telegram = service.create_discovery_telegram_object()

        assert isinstance(telegram, SystemTelegram)
        assert telegram.serial_number == "0000000000"
        assert telegram.system_function == SystemFunction.DISCOVERY
        assert telegram.data_point_id == DataPointType.NONE
        assert telegram.checksum == "FA"
        assert telegram.raw_telegram == "<S0000000000F01D00FA>"

    def test_is_discovery_response(self):
        """Test identifying discovery responses"""
        service = DiscoveryService()

        # Create mock discovery response
        discovery_reply = Mock(spec=ReplyTelegram)
        discovery_reply.system_function = SystemFunction.DISCOVERY

        assert service.is_discovery_response(discovery_reply) is True

        # Create mock non-discovery response
        other_reply = Mock(spec=ReplyTelegram)
        other_reply.system_function = SystemFunction.READ_DATAPOINT

        assert service.is_discovery_response(other_reply) is False

    def test_get_unique_devices(self):
        """Test filtering unique devices"""
        service = DiscoveryService()

        devices = [
            DeviceInfo("0020030837"),
            DeviceInfo("0020044966"),
            DeviceInfo("0020030837"),  # Duplicate
            DeviceInfo("0020042796"),
            DeviceInfo("0020044966"),  # Duplicate
        ]

        result = service.get_unique_devices(devices)

        assert len(result) == 3
        serials = [device.serial_number for device in result]
        assert "0020030837" in serials
        assert "0020044966" in serials
        assert "0020042796" in serials

    def test_validate_discovery_response_format_valid(self):
        """Test validating valid discovery response format"""
        service = DiscoveryService()

        valid_telegrams = [
            "<R0020030837F01DFM>",
            "<R0020044966F01DFK>",
            "<R0020042796F01DFN>",
            "<R1234567890F01DAB>",
        ]

        for telegram in valid_telegrams:
            assert service.validate_discovery_response_format(telegram) is True

    def test_validate_discovery_response_format_invalid(self):
        """Test validating invalid discovery response format"""
        service = DiscoveryService()

        invalid_telegrams = [
            "<R002003083F01DFM>",  # Serial too short
            "<R00200308377F01DFM>",  # Serial too long
            "<R0020030837F02DFM>",  # Wrong function
            "<R0020030837F01CFM>",  # Wrong data point
            "<R0020030837F01D>",  # Missing checksum
            "<R0020030837F01DFMX>",  # Extra characters
            "<S0020030837F01DFM>",  # System telegram, not reply
            "R0020030837F01DFM",  # Missing brackets
        ]

        for telegram in invalid_telegrams:
            assert service.validate_discovery_response_format(telegram) is False

    def test_generate_discovery_summary(self):
        """Test generating discovery summary"""
        service = DiscoveryService()

        devices = [
            DeviceInfo("0020030837", checksum_valid=True),
            DeviceInfo("0020044966", checksum_valid=True),
            DeviceInfo("0020030837", checksum_valid=True),  # Duplicate
            DeviceInfo("0020042796", checksum_valid=False),  # Invalid checksum
            DeviceInfo("0021044966", checksum_valid=True),  # Different prefix
        ]

        result = service.generate_discovery_summary(devices)

        assert result["total_responses"] == 5
        assert result["unique_devices"] == 4
        assert result["valid_checksums"] == 3
        assert result["invalid_checksums"] == 1
        assert result["success_rate"] == 75.0
        assert result["duplicate_responses"] == 1
        assert result["serial_prefixes"]["0020"] == 3
        assert result["serial_prefixes"]["0021"] == 1
        assert len(result["device_list"]) == 3  # Only valid devices

    def test_generate_discovery_summary_empty(self):
        """Test generating summary for empty device list"""
        service = DiscoveryService()

        result = service.generate_discovery_summary([])

        assert result["total_responses"] == 0
        assert result["unique_devices"] == 0
        assert result["valid_checksums"] == 0
        assert result["invalid_checksums"] == 0
        assert result["success_rate"] == 0
        assert result["duplicate_responses"] == 0
        assert result["serial_prefixes"] == {}
        assert result["device_list"] == []

    def test_format_discovery_results_empty(self):
        """Test formatting results for empty device list"""
        service = DiscoveryService()

        result = service.format_discovery_results([])
        assert result == "No devices discovered"

    def test_format_discovery_results_with_devices(self):
        """Test formatting results with devices"""
        service = DiscoveryService()

        devices = [
            DeviceInfo("0020030837", checksum_valid=True),
            DeviceInfo("0020044966", checksum_valid=False),
            DeviceInfo("0020042796", checksum_valid=True),
        ]

        result = service.format_discovery_results(devices)

        assert "=== Device Discovery Results ===" in result
        assert "Total Responses: 3" in result
        assert "Unique Devices: 3" in result
        assert "Valid Checksums: 2/3 (66.7%)" in result
        assert "✓ 0020030837" in result
        assert "✗ 0020044966" in result
        assert "✓ 0020042796" in result
        assert "0020xxxx: 3 device(s)" in result

    def test_format_discovery_results_with_duplicates(self):
        """Test formatting results with duplicate devices"""
        service = DiscoveryService()

        devices = [
            DeviceInfo("0020030837", checksum_valid=True),
            DeviceInfo("0020030837", checksum_valid=True),  # Duplicate
            DeviceInfo("0020044966", checksum_valid=True),
        ]

        result = service.format_discovery_results(devices)

        assert "Total Responses: 3" in result
        assert "Unique Devices: 2" in result
        assert "Duplicate Responses: 1" in result
