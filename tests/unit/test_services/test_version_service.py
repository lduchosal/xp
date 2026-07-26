# Copyright (c) 2025 ldvchosal
"""Unit tests for version service functionality."""

import unittest
from datetime import UTC, datetime

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_version_service import VersionService


class TestVersionService(unittest.TestCase):
    """Test version service functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.service = VersionService()

    def test_parse_version_string_valid(self) -> None:
        """Test parsing valid version strings."""
        test_cases = [
            "XP230_V1.00.04",
            "XP20_V0.01.05",
            "XP33LR_V0.04.02",
            "XP24_V0.34.03",
        ]

        for version_string in test_cases:
            with self.subTest(version_string=version_string):
                result = self.service.parse_version_string(version_string)

                assert result.success
                assert result.error is None

                product, version = version_string.split("_V")
                assert result.data["product"] == product
                assert result.data["version"] == version
                assert result.data["full_version"] == version_string
                assert result.data["formatted"] == f"{product} v{version}"
                assert result.data["valid_format"]

    def test_parse_version_string_invalid_format(self) -> None:
        """Test parsing invalid version strings."""
        test_cases = [
            "XP230_V1.00",  # Too few version parts
            "XP230_V1.00.04.05",  # Too many version parts
            "XP230_VX.YZ.AB",  # Non-numeric version
            "INVALID_FORMAT",  # No _V separator
            "XP230_1.00.04",  # Missing V prefix
            "",  # Empty string
        ]

        for version_string in test_cases:
            with self.subTest(version_string=version_string):
                result = self.service.parse_version_string(version_string)

                if not version_string or "_V" not in version_string:
                    assert not result.success
                    assert result.error is not None
                # Invalid version format but has _V
                elif version_string in {
                    "XP230_V1.00",
                    "XP230_V1.00.04.05",
                    "XP230_VX.YZ.AB",
                }:
                    assert result.success
                    assert not result.data["valid_format"]
                    assert "warning" in result.data

    def test_generate_version_request_telegram_valid(self) -> None:
        """Test generating valid version request telegrams."""
        test_cases = ["0012345011", "0012345006", "0012345010", "0000000000"]

        for serial_number in test_cases:
            with self.subTest(serial_number=serial_number):
                result = self.service.generate_version_request_telegram(serial_number)

                assert result.success
                assert result.error is None

                assert result.data["serial_number"] == serial_number
                assert result.data["function_code"] == "02"
                assert result.data["datapoint_code"] == "02"
                assert result.data["operation"] == "version_request"

                # Verify telegram format
                telegram = result.data["telegram"]
                assert telegram.startswith("<")
                assert telegram.endswith(">")
                assert f"S{serial_number}F02D02" in telegram

    def test_generate_version_request_telegram_invalid(self) -> None:
        """Test generating version request telegrams with invalid inputs."""
        test_cases = [
            ("123456789", "Serial number must be exactly 10 digits"),  # Too short
            ("12345678901", "Serial number must be exactly 10 digits"),  # Too long
            ("123456789A", "Serial number must be exactly 10 digits"),  # Non-numeric
            ("", "Serial number must be exactly 10 digits"),  # Empty
        ]

        for serial_number, expected_error in test_cases:
            with self.subTest(serial_number=serial_number):
                result = self.service.generate_version_request_telegram(serial_number)

                assert not result.success
                assert result.error is not None
                assert result.error is not None
                assert expected_error.split()[0] in result.error

    def test_validate_version_telegram_valid(self) -> None:
        """Test validating valid version request telegrams."""
        telegram = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
            checksum="FM",
            raw_telegram="<S0012345011F02D02FM>",
            timestamp=datetime.now(UTC),
            checksum_validated=True,
        )

        result = self.service.validate_version_telegram(telegram)

        assert result.success
        assert result.error is None
        assert result.data["is_version_request"]
        assert result.data["serial_number"] == "0012345011"
        assert result.data["function"] == "02"
        assert result.data["data_point"] == "02"
        assert result.data["function_description"] == "READ_DATAPOINT"
        assert result.data["data_point_description"] == "SW_VERSION"

    def test_validate_version_telegram_not_version(self) -> None:
        """Test validating non-version request telegrams."""
        telegram = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="XX",
            raw_telegram="<S0012345011F02D18XX>",
            timestamp=datetime.now(UTC),
            checksum_validated=True,
        )

        result = self.service.validate_version_telegram(telegram)

        assert result.success
        assert result.error is None
        assert not result.data["is_version_request"]
        assert result.data["data_point_description"] == "TEMPERATURE"

    def test_parse_version_reply_valid(self) -> None:
        """Test parsing valid version reply telegrams."""
        test_cases = [
            ("0012345011", "XP230_V1.00.04"),
            ("0012345006", "XP20_V0.01.05"),
            ("0012345010", "XP33LR_V0.04.02"),
            ("0012345007", "XP24_V0.34.03"),
        ]

        for serial_number, data_value in test_cases:
            with self.subTest(serial_number=serial_number, data_value=data_value):
                telegram = ReplyTelegram(
                    serial_number=serial_number,
                    system_function=SystemFunction.READ_DATAPOINT,
                    datapoint_type=DataPointType.SW_VERSION,
                    data_value=data_value,
                    checksum="XX",
                    raw_telegram=f"<R{serial_number}F02D02{data_value}XX>",
                    timestamp=datetime.now(UTC),
                    checksum_validated=True,
                )

                result = self.service.parse_version_reply(telegram)

                assert result.success
                assert result.error is None
                assert result.data["serial_number"] == serial_number
                assert result.data["checksum_valid"]

                version_info = result.data["version_info"]
                assert version_info["parsed"]

                product, version = data_value.split("_V")
                assert version_info["product"] == product
                assert version_info["version"] == version

    def test_parse_version_reply_invalid_format(self) -> None:
        """Test parsing reply telegrams with invalid version format."""
        telegram = ReplyTelegram(
            serial_number="0020000000",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
            data_value="INVALID_FORMAT",
            checksum="XX",
            raw_telegram="<R0020000000F02D02INVALID_FORMATXX>",
            timestamp=datetime.now(UTC),
            checksum_validated=True,
        )

        result = self.service.parse_version_reply(telegram)

        assert not result.success
        assert result.error is not None
        assert result.data["serial_number"] == "0020000000"
        assert result.data["raw_value"] == "INVALID_FORMAT"

    def test_parse_version_reply_not_version(self) -> None:
        """Test parsing non-version reply telegrams."""
        telegram = ReplyTelegram(
            serial_number="0020000000",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+25.0§C",
            checksum="XX",
            raw_telegram="<R0020000000F02D18+25.0§CXX>",
            timestamp=datetime.now(UTC),
            checksum_validated=True,
        )

        result = self.service.parse_version_reply(telegram)

        assert not result.success
        assert result.error is not None
        assert result.error is not None
        assert "Not a version reply" in result.error

    def test_format_version_summary_valid(self) -> None:
        """Test formatting valid version summary."""
        version_data = {
            "serial_number": "0012345011",
            "version_info": {
                "parsed": True,
                "product": "XP230",
                "version": "1.00.04",
                "full_version": "XP230_V1.00.04",
            },
            "checksum_valid": True,
        }

        summary = self.service.format_version_summary(version_data)

        assert "Device Version Information:" in summary
        assert "Serial Number: 0012345011" in summary
        assert "Product: XP230" in summary
        assert "Version: 1.00.04" in summary
        assert "Full Version: XP230_V1.00.04" in summary
        assert "Checksum: Valid (✓)" in summary

    def test_format_version_summary_invalid_checksum(self) -> None:
        """Test formatting version summary with invalid checksum."""
        version_data = {
            "serial_number": "0012345011",
            "version_info": {
                "parsed": True,
                "product": "XP230",
                "version": "1.00.04",
                "full_version": "XP230_V1.00.04",
            },
            "checksum_valid": False,
        }

        summary = self.service.format_version_summary(version_data)

        assert "Checksum: Valid (✗)" in summary

    def test_format_version_summary_parse_error(self) -> None:
        """Test formatting version summary with parse error."""
        version_data = {
            "serial_number": "0012345011",
            "version_info": {"parsed": False, "error": "Invalid format"},
        }

        summary = self.service.format_version_summary(version_data)

        assert "Version parsing failed" in summary
        assert "0012345011" in summary
        assert "Invalid format" in summary

    def test_format_version_summary_invalid_input(self) -> None:
        """Test formatting version summary with invalid input."""
        test_cases = [{"no_version_info": True}]

        for version_data in test_cases:
            with self.subTest(version_data=version_data):
                summary = self.service.format_version_summary(version_data)
                assert "No version information available" in summary


if __name__ == "__main__":
    unittest.main()
