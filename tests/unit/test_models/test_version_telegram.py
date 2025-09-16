"""Unit tests for version telegram parsing functionality."""

import unittest
from datetime import datetime

from src.xp.models.system_telegram import SystemTelegram
from src.xp.models.datapoint_type import DataPointType
from src.xp.models.system_function import SystemFunction
from src.xp.models.reply_telegram import ReplyTelegram


class TestVersionSystemTelegram(unittest.TestCase):
    """Test version-related system telegram functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.version_system_telegram = SystemTelegram(
            serial_number="0020030837",
            system_function=SystemFunction.READ_DATAPOINT,
            data_point_id=DataPointType.VERSION,
            checksum="FM",
            raw_telegram="<S0020030837F02D02FM>",
            timestamp=datetime.now(),
            checksum_validated=True,
        )

    def test_version_system_telegram_creation(self):
        """Test creating a version system telegram."""
        self.assertEqual(self.version_system_telegram.serial_number, "0020030837")
        self.assertEqual(
            self.version_system_telegram.system_function, SystemFunction.READ_DATAPOINT
        )
        self.assertEqual(
            self.version_system_telegram.data_point_id, DataPointType.VERSION
        )
        self.assertEqual(self.version_system_telegram.checksum, "FM")
        self.assertTrue(self.version_system_telegram.checksum_validated)

    def test_version_system_telegram_descriptions(self):
        """Test human-readable descriptions for version telegram."""
        self.assertEqual(
            self.version_system_telegram.function_description, "Read Data point"
        )
        self.assertEqual(self.version_system_telegram.data_point_description, "Version")

    def test_version_system_telegram_to_dict(self):
        """Test converting version system telegram to dictionary."""
        result = self.version_system_telegram.to_dict()

        self.assertEqual(result["serial_number"], "0020030837")
        self.assertEqual(result["system_function"]["code"], "02")
        self.assertEqual(result["system_function"]["description"], "Read Data point")
        self.assertEqual(result["data_point_id"]["code"], "02")
        self.assertEqual(result["data_point_id"]["description"], "Version")
        self.assertEqual(result["checksum"], "FM")
        self.assertTrue(result["checksum_validated"])
        self.assertEqual(result["telegram_type"], "system")

    def test_version_system_telegram_str(self):
        """Test string representation of version system telegram."""
        expected = "System Telegram: Read Data point for Version from device 0020030837"
        self.assertEqual(str(self.version_system_telegram), expected)


class TestVersionReplyTelegram(unittest.TestCase):
    """Test version-related reply telegram functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.version_reply_telegram = ReplyTelegram(
            serial_number="0020030837",
            system_function=SystemFunction.READ_DATAPOINT,
            data_point_id=DataPointType.VERSION,
            data_value="XP230_V1.00.04",
            checksum="FI",
            raw_telegram="<R0020030837F02D02XP230_V1.00.04FI>",
            timestamp=datetime.now(),
            checksum_validated=True,
        )

        self.invalid_version_reply = ReplyTelegram(
            serial_number="0020044966",
            system_function=SystemFunction.READ_DATAPOINT,
            data_point_id=DataPointType.VERSION,
            data_value="INVALID_FORMAT",
            checksum="XX",
            raw_telegram="<R0020044966F02D02INVALID_FORMATXX>",
            timestamp=datetime.now(),
            checksum_validated=False,
        )

    def test_version_reply_telegram_creation(self):
        """Test creating a version reply telegram."""
        self.assertEqual(self.version_reply_telegram.serial_number, "0020030837")
        self.assertEqual(
            self.version_reply_telegram.system_function, SystemFunction.READ_DATAPOINT
        )
        self.assertEqual(
            self.version_reply_telegram.data_point_id, DataPointType.VERSION
        )
        self.assertEqual(self.version_reply_telegram.data_value, "XP230_V1.00.04")
        self.assertEqual(self.version_reply_telegram.checksum, "FI")
        self.assertTrue(self.version_reply_telegram.checksum_validated)

    def test_version_reply_telegram_descriptions(self):
        """Test human-readable descriptions for version reply telegram."""
        self.assertEqual(
            self.version_reply_telegram.function_description, "Data Response"
        )
        self.assertEqual(self.version_reply_telegram.data_point_description, "Version")

    def test_version_reply_telegram_parsed_value_valid(self):
        """Test parsing valid version value."""
        parsed = self.version_reply_telegram.parsed_value

        self.assertTrue(parsed["parsed"])
        self.assertEqual(parsed["product"], "XP230")
        self.assertEqual(parsed["version"], "1.00.04")
        self.assertEqual(parsed["full_version"], "XP230_V1.00.04")
        self.assertEqual(parsed["formatted"], "XP230 v1.00.04")
        self.assertEqual(parsed["raw_value"], "XP230_V1.00.04")

    def test_version_reply_telegram_parsed_value_invalid(self):
        """Test parsing invalid version value."""
        parsed = self.invalid_version_reply.parsed_value

        self.assertFalse(parsed["parsed"])
        self.assertEqual(parsed["full_version"], "INVALID_FORMAT")
        self.assertEqual(parsed["formatted"], "INVALID_FORMAT")
        self.assertEqual(parsed["raw_value"], "INVALID_FORMAT")
        self.assertIn("error", parsed)

    def test_version_reply_telegram_to_dict(self):
        """Test converting version reply telegram to dictionary."""
        result = self.version_reply_telegram.to_dict()

        self.assertEqual(result["serial_number"], "0020030837")
        self.assertEqual(result["system_function"]["code"], "02")
        self.assertEqual(result["system_function"]["description"], "Data Response")
        self.assertEqual(result["data_point_id"]["code"], "02")
        self.assertEqual(result["data_point_id"]["description"], "Version")
        self.assertEqual(result["data_value"]["raw"], "XP230_V1.00.04")
        self.assertTrue(result["data_value"]["parsed"]["parsed"])
        self.assertEqual(result["data_value"]["parsed"]["product"], "XP230")
        self.assertEqual(result["checksum"], "FI")
        self.assertTrue(result["checksum_validated"])
        self.assertEqual(result["telegram_type"], "reply")

    def test_version_reply_telegram_str_valid(self):
        """Test string representation of version reply telegram with valid version."""
        expected = "Reply Telegram: Data Response for Version = XP230 v1.00.04 from device 0020030837"
        self.assertEqual(str(self.version_reply_telegram), expected)

    def test_version_reply_telegram_str_invalid(self):
        """Test string representation of version reply telegram with invalid version."""
        expected = "Reply Telegram: Data Response for Version = INVALID_FORMAT from device 0020044966"
        self.assertEqual(str(self.invalid_version_reply), expected)

    def test_version_formats(self):
        """Test various version formats from the specification."""
        test_cases = [
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
                    data_point_id=DataPointType.VERSION,
                    data_value=data_value,
                    checksum="XX",
                    raw_telegram=f"<R0020000000F02D02{data_value}XX>",
                    timestamp=datetime.now(),
                    checksum_validated=True,
                )

                parsed = telegram.parsed_value
                self.assertEqual(parsed["parsed"], expected["parsed"])

                if expected["parsed"]:
                    self.assertEqual(parsed["product"], expected["product"])
                    self.assertEqual(parsed["version"], expected["version"])
                    self.assertEqual(parsed["full_version"], data_value)


if __name__ == "__main__":
    unittest.main()
