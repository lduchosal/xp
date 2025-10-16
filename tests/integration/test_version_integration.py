"""Integration tests for version parsing functionality."""

import unittest

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService
from xp.services.telegram.telegram_version_service import VersionService


class TestVersionIntegration(unittest.TestCase):
    """Integration tests for version telegram parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.telegram_service = TelegramService()
        self.version_service = VersionService()

    def test_parse_version_system_telegram_from_spec(self):
        """Test parsing version system telegram from specification example."""
        raw_telegram = "<S0012345011F02D02FM>"

        parsed = self.telegram_service.parse_system_telegram(raw_telegram)

        self.assertEqual(parsed.serial_number, "0012345011")
        self.assertEqual(parsed.system_function, SystemFunction.READ_DATAPOINT)
        self.assertEqual(parsed.datapoint_type, DataPointType.SW_VERSION)
        self.assertEqual(parsed.checksum, "FM")
        self.assertEqual(parsed.raw_telegram, raw_telegram)

        # Verify it's a version request using version service
        validation = self.version_service.validate_version_telegram(parsed)
        self.assertTrue(validation.success)
        self.assertTrue(validation.data["is_version_request"])

    def test_parse_version_reply_telegrams_from_spec(self):
        """Test parsing version reply telegrams from specification examples."""
        test_cases = [
            ("<R0012345011F02D02XP230_V1.00.04FI>", "XP230", "1.00.04"),
            ("<R0012345002F02D02XP20_V0.01.05GK>", "XP20", "0.01.05"),
            ("<R0012345003F02D02XP33LR_V0.04.02HF>", "XP33LR", "0.04.02"),
            ("<R0012345004F02D02XP24_V0.34.03GA>", "XP24", "0.34.03"),
            ("<R0012345008F02D02XP24_V0.34.03GK>", "XP24", "0.34.03"),
            ("<R0012345009F02D02XP24_V0.34.03GG>", "XP24", "0.34.03"),
            ("<R0012345007F02D02XP24_V0.34.03GJ>", "XP24", "0.34.03"),
            ("<R0012345010F02D02XP20_V0.01.05GO>", "XP20", "0.01.05"),
            ("<R0012345006F02D02XP24_V0.34.03GI>", "XP24", "0.34.03"),
            ("<R0012345005F02D02XP24_V0.34.03GL>", "XP24", "0.34.03"),
        ]

        for raw_telegram, expected_product, expected_version in test_cases:
            with self.subTest(raw_telegram=raw_telegram):
                # Parse using telegram service
                parsed = self.telegram_service.parse_reply_telegram(raw_telegram)

                # Verify basic parsing
                self.assertEqual(parsed.system_function, SystemFunction.READ_DATAPOINT)
                self.assertEqual(parsed.datapoint_type, DataPointType.SW_VERSION)
                self.assertEqual(parsed.raw_telegram, raw_telegram)

                # Verify version parsing using built-in reply telegram parser
                version_data = parsed.parse_datapoint_value
                self.assertTrue(version_data["parsed"])
                self.assertEqual(version_data["product"], expected_product)
                self.assertEqual(version_data["version"], expected_version)
                self.assertEqual(
                    version_data["full_version"],
                    f"{expected_product}_V{expected_version}",
                )

                # Verify using version service
                version_result = self.version_service.parse_version_reply(parsed)
                self.assertTrue(version_result.success)
                self.assertEqual(
                    version_result.data["version_info"]["product"], expected_product
                )
                self.assertEqual(
                    version_result.data["version_info"]["version"], expected_version
                )

    def test_auto_detect_version_telegrams(self):
        """Test auto-detecting version telegrams using the generic parse method."""
        test_cases = [
            ("<S0012345011F02D02FM>", "S"),
            ("<R0012345011F02D02XP230_V1.00.04FI>", "R"),
        ]

        for raw_telegram, expected_type in test_cases:
            with self.subTest(raw_telegram=raw_telegram):
                parsed = self.telegram_service.parse_telegram(raw_telegram)

                self.assertEqual(parsed.to_dict()["telegram_type"], expected_type)

                if expected_type == "s":
                    assert isinstance(parsed, SystemTelegram)
                    validation = self.version_service.validate_version_telegram(parsed)
                    self.assertTrue(validation.success)
                    self.assertTrue(validation.data["is_version_request"])
                elif expected_type == "r":
                    assert isinstance(parsed, ReplyTelegram)
                    version_result = self.version_service.parse_version_reply(parsed)
                    self.assertTrue(version_result.success)
                    self.assertTrue(version_result.data["version_info"]["parsed"])

    def test_generate_and_parse_version_request(self):
        """Test generating version request and then parsing it back."""
        serial_number = "0012345011"

        # Generate version request telegram
        generation_result = self.version_service.generate_version_request_telegram(
            serial_number
        )
        self.assertTrue(generation_result.success)

        generated_telegram = generation_result.data["telegram"]

        # Parse the generated telegram
        parsed = self.telegram_service.parse_system_telegram(generated_telegram)

        # Verify it parsed correctly
        self.assertEqual(parsed.serial_number, serial_number)
        self.assertEqual(parsed.system_function, SystemFunction.READ_DATAPOINT)
        self.assertEqual(parsed.datapoint_type, DataPointType.SW_VERSION)

        # Verify it's recognized as a version request
        validation = self.version_service.validate_version_telegram(parsed)
        self.assertTrue(validation.success)
        self.assertTrue(validation.data["is_version_request"])

    def test_invalid_version_telegram_handling(self):
        """Test handling of invalid version telegrams."""
        invalid_cases = [
            "<R0012345011F02D02INVALID_FORMATXX>",  # Invalid version format
            "<R0012345011F02D18+25.0§CXX>",  # Not a version telegram (temperature)
            "<S0012345011F02D18XX>",  # System telegram but not version
            "<INVALID>",  # Invalid telegram format
        ]

        for raw_telegram in invalid_cases:
            with self.subTest(raw_telegram=raw_telegram):
                try:
                    parsed = self.telegram_service.parse_telegram(raw_telegram)

                    if hasattr(parsed, "data_value"):  # Reply telegram
                        assert isinstance(parsed, ReplyTelegram)
                        if parsed.datapoint_type == DataPointType.SW_VERSION:
                            version_result = self.version_service.parse_version_reply(
                                parsed
                            )
                            if "INVALID_FORMAT" in raw_telegram:
                                self.assertFalse(version_result.success)
                        else:
                            # Not a version telegram - should fail version parsing
                            assert isinstance(parsed, ReplyTelegram)
                            version_result = self.version_service.parse_version_reply(
                                parsed
                            )
                            self.assertFalse(version_result.success)
                    elif hasattr(parsed, "system_function"):  # System telegram
                        assert isinstance(parsed, SystemTelegram)
                        validation = self.version_service.validate_version_telegram(
                            parsed
                        )
                        self.assertTrue(validation.success)
                        assert hasattr(parsed, "datapoint_type")
                        if parsed.datapoint_type != DataPointType.SW_VERSION:
                            self.assertFalse(validation.data["is_version_request"])

                except TelegramParsingError:
                    # Expected for invalid telegram formats
                    self.assertIn("INVALID", raw_telegram)

    def test_version_telegram_formatting(self):
        """Test formatting of version telegrams for display."""
        raw_telegram = "<R0012345011F02D02XP230_V1.00.04FI>"

        # Parse telegram
        parsed = self.telegram_service.parse_reply_telegram(raw_telegram)

        # Parse version information
        version_result = self.version_service.parse_version_reply(parsed)
        self.assertTrue(version_result.success)

        # Format for display
        summary = self.version_service.format_version_summary(version_result.data)

        self.assertIn("Device Version Information:", summary)
        self.assertIn("Serial Number: 0012345011", summary)
        self.assertIn("Product: XP230", summary)
        self.assertIn("Version: 1.00.04", summary)
        self.assertIn("Full Version: XP230_V1.00.04", summary)

    def test_version_parsing_edge_cases(self):
        """Test edge cases in version parsing."""
        edge_cases = [
            # Version with additional underscores in product name
            ("<R0020000000F02D02XP_33_LR_V1.23.45XX>", "XP_33_LR", "1.23.45"),
            # Single character product
            ("<R0020000000F02D02A_V0.00.01XX>", "A", "0.00.01"),
            # Long product name
            (
                "<R0020000000F02D02VERYLONGPRODUCTNAME_V9.99.99XX>",
                "VERYLONGPRODUCTNAME",
                "9.99.99",
            ),
        ]

        for raw_telegram, expected_product, expected_version in edge_cases:
            with self.subTest(raw_telegram=raw_telegram):
                try:
                    parsed = self.telegram_service.parse_reply_telegram(raw_telegram)
                    version_data = parsed.parse_datapoint_value

                    self.assertTrue(version_data["parsed"])
                    self.assertEqual(version_data["product"], expected_product)
                    self.assertEqual(version_data["version"], expected_version)

                except Exception as e:
                    self.fail(f"Failed to parse {raw_telegram}: {e}")

    def test_telegram_service_format_version_reply(self):
        """Test that telegram service correctly formats version reply summaries."""
        raw_telegram = "<R0012345011F02D02XP230_V1.00.04FI>"

        parsed = self.telegram_service.parse_reply_telegram(raw_telegram)
        summary = self.telegram_service.format_reply_telegram_summary(parsed)

        self.assertIn("Reply Telegram: READ_DATAPOINT", summary)
        self.assertIn("for SW_VERSION = XP230 v1.00.04", summary)
        self.assertIn("from device 0012345011", summary)
        self.assertIn("Data: XP230 v1.00.04", summary)
        self.assertIn(f"Raw: {raw_telegram}", summary)


if __name__ == "__main__":
    unittest.main()
