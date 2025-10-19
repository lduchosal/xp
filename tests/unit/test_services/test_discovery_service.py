"""Tests for DiscoverService."""

from unittest.mock import Mock

from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_discover_service import (
    DeviceInfo,
    TelegramDiscoverService,
)


class TestDeviceInfo:
    """Test cases for DeviceInfo class."""

    def test_init(self):
        """Test DeviceInfo initialization."""
        device = DeviceInfo("0012345011")
        assert device.serial_number == "0012345011"
        assert device.checksum_valid is True
        assert device.raw_telegram == ""

    def test_init_with_all_params(self):
        """Test DeviceInfo initialization with all parameters."""
        device = DeviceInfo(
            "0012345011", checksum_valid=False, raw_telegram="<R0012345011F01DFM>"
        )
        assert device.serial_number == "0012345011"
        assert device.checksum_valid is False
        assert device.raw_telegram == "<R0012345011F01DFM>"

    def test_str_representation(self):
        """Test string representation."""
        device_valid = DeviceInfo("0012345011", checksum_valid=True)
        device_invalid = DeviceInfo("0012345011", checksum_valid=False)

        assert str(device_valid) == "Device 0012345011 (✓)"
        assert str(device_invalid) == "Device 0012345011 (✗)"

    def test_repr(self):
        """Test repr representation."""
        device = DeviceInfo("0012345011", checksum_valid=False)
        assert repr(device) == "DeviceInfo(serial='0012345011', checksum_valid=False)"

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = DeviceInfo(
            "0012345011", checksum_valid=True, raw_telegram="<R0012345011F01DFM>"
        ).to_dict()

        expected = {
            "serial_number": "0012345011",
            "checksum_valid": True,
            "raw_telegram": "<R0012345011F01DFM>",
        }
        assert result == expected


class TestDiscoverService:
    """Test cases for DiscoverService."""

    def test_init(self):
        """Test initialization."""
        service = TelegramDiscoverService()
        assert isinstance(service, TelegramDiscoverService)

    def test_generate_discover_telegram(self):
        """Test generating discover broadcast telegram."""
        result = TelegramDiscoverService().generate_discover_telegram()
        assert result == "<S0000000000F01D00FA>"

    def test_create_discover_telegram_object(self):
        """Test creating SystemTelegram object for discover."""
        telegram = TelegramDiscoverService().create_discover_telegram_object()

        assert isinstance(telegram, SystemTelegram)
        assert telegram.serial_number == "0000000000"
        assert telegram.system_function == SystemFunction.DISCOVERY
        assert telegram.datapoint_type is None
        assert telegram.checksum == "FA"
        assert telegram.raw_telegram == "<S0000000000F01D00FA>"

    def test_is_discover_response(self):
        """Test identifying discover responses."""
        service = TelegramDiscoverService()

        # Create mock discover response
        discover_reply = Mock(spec=ReplyTelegram)
        discover_reply.system_function = SystemFunction.DISCOVERY

        assert service.is_discover_response(discover_reply) is True

        # Create mock non-discover response
        other_reply = Mock(spec=ReplyTelegram)
        other_reply.system_function = SystemFunction.READ_DATAPOINT

        assert service.is_discover_response(other_reply) is False

    def test_get_unique_devices(self):
        """Test filtering unique devices."""
        service = TelegramDiscoverService()

        devices = [
            DeviceInfo("0012345011"),
            DeviceInfo("0012345006"),
            DeviceInfo("0012345011"),  # Duplicate
            DeviceInfo("0012345003"),
            DeviceInfo("0012345006"),  # Duplicate
        ]

        result = service.get_unique_devices(devices)

        assert len(result) == 3
        serials = [device.serial_number for device in result]
        assert "0012345011" in serials
        assert "0012345006" in serials
        assert "0012345003" in serials

    def test_validate_discover_response_format_valid(self):
        """Test validating valid discover response format."""
        service = TelegramDiscoverService()

        valid_telegrams = [
            "<R0012345011F01DFM>",
            "<R0012345006F01DFK>",
            "<R0012345003F01DFN>",
            "<R1234567890F01DAB>",
        ]

        for telegram in valid_telegrams:
            assert service.validate_discover_response_format(telegram) is True

    def test_validate_discover_response_format_invalid(self):
        """Test validating invalid discover response format."""
        service = TelegramDiscoverService()

        invalid_telegrams = [
            "<R002003083F01DFM>",  # Serial too short
            "<R00123450117F01DFM>",  # Serial too long
            "<R0012345011F02DFM>",  # Wrong function
            "<R0012345011F01CFM>",  # Wrong data point
            "<R0012345011F01D>",  # Missing checksum
            "<R0012345011F01DFMX>",  # Extra characters
            "<S0012345011F01DFM>",  # System telegram, not reply
            "R0012345011F01DFM",  # Missing brackets
        ]

        for telegram in invalid_telegrams:
            assert service.validate_discover_response_format(telegram) is False

    def test_generate_discover_summary(self):
        """Test generating discover summary."""
        service = TelegramDiscoverService()

        devices = [
            DeviceInfo("0012345011", checksum_valid=True),
            DeviceInfo("0012345006", checksum_valid=True),
            DeviceInfo("0012345011", checksum_valid=True),  # Duplicate
            DeviceInfo("0012345003", checksum_valid=False),  # Invalid checksum
            DeviceInfo("0021044966", checksum_valid=True),  # Different prefix
        ]

        result = service.generate_discover_summary(devices)

        assert result["total_responses"] == 5
        assert result["unique_devices"] == 4
        assert result["valid_checksums"] == 3
        assert result["invalid_checksums"] == 1
        assert result["success_rate"] == 75.0
        assert result["duplicate_responses"] == 1
        assert result["serial_prefixes"]["0012"] == 3
        assert result["serial_prefixes"]["0021"] == 1
        assert len(result["device_list"]) == 3  # Only valid devices

    def test_generate_discover_summary_empty(self):
        """Test generating summary for empty device list."""
        result = TelegramDiscoverService().generate_discover_summary([])

        assert result["total_responses"] == 0
        assert result["unique_devices"] == 0
        assert result["valid_checksums"] == 0
        assert result["invalid_checksums"] == 0
        assert result["success_rate"] == 0
        assert result["duplicate_responses"] == 0
        assert result["serial_prefixes"] == {}
        assert result["device_list"] == []

    def test_format_discover_results_empty(self):
        """Test formatting results for empty device list."""
        result = TelegramDiscoverService().format_discover_results([])
        assert result == "No devices discovered"

    def test_format_discover_results_with_devices(self):
        """Test formatting results with devices."""
        service = TelegramDiscoverService()

        devices = [
            DeviceInfo("0012345011", checksum_valid=True),
            DeviceInfo("0012345006", checksum_valid=False),
            DeviceInfo("0012345003", checksum_valid=True),
        ]

        result = service.format_discover_results(devices)

        assert "=== Device Discover Results ===" in result
        assert "Total Responses: 3" in result
        assert "Unique Devices: 3" in result
        assert "Valid Checksums: 2/3 (66.7%)" in result
        assert "✓ 0012345011" in result
        assert "✗ 0012345006" in result
        assert "✓ 0012345003" in result
        assert "0012xxxx: 3 device(s)" in result

    def test_format_discover_results_with_duplicates(self):
        """Test formatting results with duplicate devices."""
        service = TelegramDiscoverService()

        devices = [
            DeviceInfo("0012345011", checksum_valid=True),
            DeviceInfo("0012345011", checksum_valid=True),  # Duplicate
            DeviceInfo("0012345006", checksum_valid=True),
        ]

        result = service.format_discover_results(devices)

        assert "Total Responses: 3" in result
        assert "Unique Devices: 2" in result
        assert "Duplicate Responses: 1" in result
