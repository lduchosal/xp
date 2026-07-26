# Copyright (c) 2025 ldvchosal
"""Unit tests for version telegram parsing functionality."""

import unittest
from datetime import UTC, datetime
from typing import Any

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram


class TestVersionSystemTelegram(unittest.TestCase):
    """Test version-related system telegram functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.version_system_telegram = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
            checksum="FM",
            raw_telegram="<S0012345011F02D02FM>",
            timestamp=datetime.now(UTC),
            checksum_validated=True,
        )

    def test_version_system_telegram_creation(self) -> None:
        """Test creating a version system telegram."""
        assert self.version_system_telegram.serial_number == "0012345011"
        assert (
            self.version_system_telegram.system_function
            == SystemFunction.READ_DATAPOINT
        )
        assert self.version_system_telegram.datapoint_type == DataPointType.SW_VERSION
        assert self.version_system_telegram.checksum == "FM"
        assert self.version_system_telegram.checksum_validated

    def test_version_system_telegram_descriptions(self) -> None:
        """Test human-readable descriptions for version telegram."""
        assert self.version_system_telegram.system_function is not None
        assert self.version_system_telegram.datapoint_type is not None
        assert self.version_system_telegram.system_function.name == "READ_DATAPOINT"
        assert self.version_system_telegram.datapoint_type.name == "SW_VERSION"

    def test_version_system_telegram_to_dict(self) -> None:
        """Test converting version system telegram to dictionary."""
        result = self.version_system_telegram.to_dict()

        assert result["serial_number"] == "0012345011"
        assert result["system_function"]["code"] == "02"
        assert result["system_function"]["description"] == "READ_DATAPOINT"
        assert result["datapoint_type"]["code"] == "02"
        assert result["datapoint_type"]["description"] == "SW_VERSION"
        assert result["checksum"] == "FM"
        assert result["checksum_validated"]
        assert result["telegram_type"] == "S"

    def test_version_system_telegram_str(self) -> None:
        """Test string representation of version system telegram."""
        expected = (
            "System Telegram: READ_DATAPOINT with data SW_VERSION "
            "from device 0012345011"
        )
        assert str(self.version_system_telegram) == expected


class TestVersionReplyTelegram(unittest.TestCase):
    """Test version-related reply telegram functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.version_reply_telegram = ReplyTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
            data_value="XP230_V1.00.04",
            checksum="FI",
            raw_telegram="<R0012345011F02D02XP230_V1.00.04FI>",
            timestamp=datetime.now(UTC),
            checksum_validated=True,
        )

        self.invalid_version_reply = ReplyTelegram(
            serial_number="0012345006",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
            data_value="INVALID_FORMAT",
            checksum="XX",
            raw_telegram="<R0012345006F02D02INVALID_FORMATXX>",
            timestamp=datetime.now(UTC),
            checksum_validated=False,
        )

    def test_version_reply_telegram_creation(self) -> None:
        """Test creating a version reply telegram."""
        assert self.version_reply_telegram.serial_number == "0012345011"
        assert (
            self.version_reply_telegram.system_function == SystemFunction.READ_DATAPOINT
        )
        assert self.version_reply_telegram.datapoint_type == DataPointType.SW_VERSION
        assert self.version_reply_telegram.data_value == "XP230_V1.00.04"
        assert self.version_reply_telegram.checksum == "FI"
        assert self.version_reply_telegram.checksum_validated

    def test_version_reply_telegram_descriptions(self) -> None:
        """Test human-readable descriptions for version reply telegram."""
        assert self.version_reply_telegram.system_function is not None
        assert self.version_reply_telegram.system_function.name == "READ_DATAPOINT"
        assert self.version_reply_telegram.datapoint_type is not None
        assert self.version_reply_telegram.datapoint_type.name == "SW_VERSION"

    def test_version_reply_telegram_parsed_value_valid(self) -> None:
        """Test parsing valid version value."""
        parsed = self.version_reply_telegram.parse_datapoint_value

        assert parsed["parsed"]
        assert parsed["product"] == "XP230"
        assert parsed["version"] == "1.00.04"
        assert parsed["full_version"] == "XP230_V1.00.04"
        assert parsed["formatted"] == "XP230 v1.00.04"
        assert parsed["raw_value"] == "XP230_V1.00.04"

    def test_version_reply_telegram_parsed_value_invalid(self) -> None:
        """Test parsing invalid version value."""
        parsed = self.invalid_version_reply.parse_datapoint_value

        assert not parsed["parsed"]
        assert parsed["full_version"] == "INVALID_FORMAT"
        assert parsed["formatted"] == "INVALID_FORMAT"
        assert parsed["raw_value"] == "INVALID_FORMAT"
        assert "error" in parsed

    def test_version_reply_telegram_to_dict(self) -> None:
        """Test converting version reply telegram to dictionary."""
        result = self.version_reply_telegram.to_dict()

        assert result["serial_number"] == "0012345011"
        assert result["system_function"]["code"] == "02"
        assert result["system_function"]["description"] == "READ_DATAPOINT"
        assert result["datapoint_type"]["code"] == "02"
        assert result["datapoint_type"]["description"] == "SW_VERSION"
        assert result["data_value"]["raw"] == "XP230_V1.00.04"
        assert result["data_value"]["parsed"]["parsed"]
        assert result["data_value"]["parsed"]["product"] == "XP230"
        assert result["checksum"] == "FI"
        assert result["checksum_validated"]
        assert result["telegram_type"] == "R"

    def test_version_formats(self) -> None:
        """Test various version formats from the specification."""
        test_cases: list[tuple[str, dict[str, Any]]] = [
            (
                "XP230_V1.00.04",
                {"product": "XP230", "version": "1.00.04", "parsed": True},
            ),
            (
                "XP20_V0.01.05",
                {"product": "XP20", "version": "0.01.05", "parsed": True},
            ),
            (
                "XP33LR_V0.04.02",
                {"product": "XP33LR", "version": "0.04.02", "parsed": True},
            ),
            (
                "XP24_V0.34.03",
                {"product": "XP24", "version": "0.34.03", "parsed": True},
            ),
            ("INVALID", {"parsed": False}),
            ("XP24_INVALID", {"parsed": False}),
        ]

        for data_value, expected in test_cases:
            with self.subTest(data_value=data_value):
                telegram = ReplyTelegram(
                    serial_number="0020000000",
                    system_function=SystemFunction.READ_DATAPOINT,
                    datapoint_type=DataPointType.SW_VERSION,
                    data_value=data_value,
                    checksum="XX",
                    raw_telegram=f"<R0020000000F02D02{data_value}XX>",
                    timestamp=datetime.now(UTC),
                    checksum_validated=True,
                )

                parsed = telegram.parse_datapoint_value
                assert parsed["parsed"] == expected["parsed"]

                if expected["parsed"]:
                    assert parsed["product"] == expected["product"]
                    assert parsed["version"] == expected["version"]
                    assert parsed["full_version"] == data_value


if __name__ == "__main__":
    unittest.main()
