"""Unit tests for XP24ActionService."""

from unittest.mock import patch

import pytest

from xp.models.telegram.action_type import ActionType
from xp.models.telegram.output_telegram import OutputTelegram
from xp.services.telegram.telegram_output_service import (
    TelegramOutputService,
    XPOutputError,
)
from xp.services.telegram.telegram_service import TelegramService


class TestXP24ActionService:
    """Test cases for XP24ActionService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramOutputService(telegram_service=TelegramService())

    def test_validate_output_number_valid(self):
        """Test validate_output_number with valid inputs."""
        # Should not raise for valid inputs
        self.service.validate_output_number(0)
        self.service.validate_output_number(1)
        self.service.validate_output_number(2)
        self.service.validate_output_number(3)

    def test_validate_output_number_invalid_range(self):
        """Test validate_output_number with invalid ranges."""
        with pytest.raises(XPOutputError, match="Invalid output number: -1"):
            self.service.validate_output_number(-1)

        with pytest.raises(XPOutputError, match="Invalid output number: 500"):
            self.service.validate_output_number(500)

        with pytest.raises(XPOutputError, match="Invalid output number: 100"):
            self.service.validate_output_number(100)

    def test_validate_serial_number_valid(self):
        """Test validate_serial_number with valid serial numbers."""
        # Should not raise for valid serial numbers
        self.service.validate_serial_number("0012345008")
        self.service.validate_serial_number("1234567890")
        self.service.validate_serial_number("0000000000")

    def test_validate_serial_number_invalid_length(self):
        """Test validate_serial_number with invalid lengths."""
        with pytest.raises(XPOutputError, match="Invalid serial number: 123456789"):
            self.service.validate_serial_number("123456789")  # 9 digits

        with pytest.raises(XPOutputError, match="Invalid serial number: 12345678901"):
            self.service.validate_serial_number("12345678901")  # 11 digits

    def test_validate_serial_number_invalid_characters(self):
        """Test validate_serial_number with non-numeric characters."""
        with pytest.raises(XPOutputError, match="Invalid serial number: 002004496A"):
            self.service.validate_serial_number("002004496A")

        with pytest.raises(XPOutputError, match="Invalid serial number: 0020-44964"):
            self.service.validate_serial_number("0020-44964")

    # Telegram generation tests

    @patch("xp.services.telegram.telegram_output_service.calculate_checksum")
    def test_generate_action_telegram_press(self, mock_checksum):
        """Test generate_action_telegram for PRESS action."""
        mock_checksum.return_value = "FN"

        result = self.service.generate_system_action_telegram(
            "0012345008", 0, ActionType.OFF_PRESS
        )

        assert result == "<S0012345008F27D00AAFN>"
        mock_checksum.assert_called_once_with("S0012345008F27D00AA")

    @patch("xp.services.telegram.telegram_output_service.calculate_checksum")
    def test_generate_action_telegram_release(self, mock_checksum):
        """Test generate_action_telegram for RELEASE action."""
        mock_checksum.return_value = "FB"

        result = self.service.generate_system_action_telegram(
            "0012345008", 3, ActionType.ON_RELEASE
        )

        assert result == "<S0012345008F27D03ABFB>"
        mock_checksum.assert_called_once_with("S0012345008F27D03AB")

    def test_generate_action_telegram_invalid_serial(self):
        """Test generate_action_telegram with invalid serial number."""
        with pytest.raises(XPOutputError):
            self.service.generate_system_action_telegram("123", 0, ActionType.OFF_PRESS)

    def test_generate_action_telegram_invalid_input(self):
        """Test generate_action_telegram with invalid input number."""
        with pytest.raises(XPOutputError):
            self.service.generate_system_action_telegram(
                "0012345008", 500, ActionType.OFF_PRESS
            )

    def test_generate_status_telegram_invalid_serial(self):
        """Test generate_status_telegram with invalid serial number."""
        with pytest.raises(XPOutputError):
            self.service.generate_system_status_telegram("invalid")

    # Telegram parsing tests

    def test_parse_action_telegram_empty(self):
        """Test parse_action_telegram with empty string."""
        with pytest.raises(XPOutputError, match="Empty telegram string"):
            self.service.parse_system_telegram("")

    def test_parse_action_telegram_invalid_format(self):
        """Test parse_action_telegram with invalid format."""
        with pytest.raises(XPOutputError, match="Invalid XP24 action telegram format"):
            self.service.parse_system_telegram("<E14L00I02MAK>")  # Event telegram

    def test_parse_action_telegram_invalid_input_range(self):
        """Test parse_action_telegram with invalid input number."""
        with pytest.raises(
            XPOutputError,
            match="Invalid XP24 action telegram format: <S0012345008F27D500AAFN>",
        ):
            self.service.parse_system_telegram("<S0012345008F27D500AAFN>")

    def test_parse_action_telegram_invalid_action_code(self):
        """Test parse_action_telegram with invalid action code."""
        with pytest.raises(
            XPOutputError,
            match="Invalid XP24 action telegram format: <S0012345008F27D01XXFN>",
        ):
            self.service.parse_system_telegram("<S0012345008F27D01XXFN>")

    # Checksum validation tests

    def test_parse_status_response_valid(self):
        """Test parse_status_response with valid response."""
        result = self.service.parse_status_response("<R0012345008F02D12xxxx1110FJ>")

        expected = [False, True, True, True]
        assert result == expected

    def test_parse_status_response_all_on(self):
        """Test parse_status_response with all inputs ON."""
        result = self.service.parse_status_response("<R0012345008F02D12xxxx1111FJ>")

        expected = [True, True, True, True]
        assert result == expected

    def test_parse_status_response_all_off(self):
        """Test parse_status_response with all inputs OFF."""
        result = self.service.parse_status_response("<R0012345008F02D12xxxx0000FJ>")
        expected = [False, False, False, False]
        assert result == expected

    def test_parse_status_response_empty(self):
        """Test parse_status_response with empty string."""
        with pytest.raises(XPOutputError, match="Empty status response telegram"):
            self.service.parse_status_response("")

    def test_parse_status_response_invalid_format(self):
        """Test parse_status_response with invalid format."""
        with pytest.raises(XPOutputError, match="Not a DataPoint telegram"):
            self.service.parse_status_response("<R0012345008F18DFA>")  # ACK telegram

    def test_parse_status_response_invalid_bits_length(self):
        """Test parse_status_response with invalid status bits length."""
        with pytest.raises(XPOutputError, match="Not a module_output_state telegram"):
            self.service.parse_status_response(
                "<R0012345008F02D12xxxx111FJ>"
            )  # Only 3 bits

    # Formatting tests

    def test_format_status_summary(self):
        """Test format_status_summary."""
        status = {0: True, 1: False, 2: True, 3: False}

        result = self.service.format_status_summary(status)

        expected = (
            "XP24 Output Status:\n"
            "  Output 0: ON\n"
            "  Output 1: OFF\n"
            "  Output 2: ON\n"
            "  Output 3: OFF"
        )
        assert result == expected

    def test_format_action_summary_with_validation(self):
        """Test format_action_summary with checksum validation."""
        telegram = OutputTelegram(
            serial_number="0012345008",
            output_number=1,
            action_type=ActionType.OFF_PRESS,
            checksum="FN",
            raw_telegram="<S0012345008F27D01AAFN>",
            checksum_validated=True,
        )

        result = self.service.format_action_summary(telegram)

        assert (
            "XP Output: XP Output: Press (Make) on Input 1 for device 0012345008"
            in result
        )
        assert "Raw: <S0012345008F27D01AAFN>" in result
        assert "Checksum: FN (✓)" in result

    def test_format_action_summary_without_validation(self):
        """Test format_action_summary without checksum validation."""
        telegram = OutputTelegram(
            serial_number="0012345008",
            output_number=2,
            action_type=ActionType.ON_RELEASE,
            checksum="FB",
            raw_telegram="<S0012345008F27D02ABFB>",
            checksum_validated=None,
        )

        result = self.service.format_action_summary(telegram)

        assert "Checksum: FB" in result
        assert "✓" not in result
        assert "✗" not in result

    def test_format_action_summary_failed_validation(self):
        """Test format_action_summary with failed checksum validation."""
        telegram = OutputTelegram(
            serial_number="0012345008",
            output_number=0,
            action_type=ActionType.OFF_PRESS,
            checksum="XX",
            raw_telegram="<S0012345008F27D00AAXX>",
            checksum_validated=False,
        )

        result = self.service.format_action_summary(telegram)

        assert "Checksum: XX (✗)" in result
