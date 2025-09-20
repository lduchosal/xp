"""Unit tests for XP24ActionService."""

import pytest
from unittest.mock import patch

from xp.services.telegram_input_service import TelegramInputService, XPInputError
from xp.models.input_telegram import InputTelegram
from xp.models.action_type import ActionType


class TestXP24ActionService:
    """Test cases for XP24ActionService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramInputService()

    def test_constants(self):
        """Test service constants."""
        assert self.service.MAX_INPUTS == 4

    # Input validation tests

    def test_validate_input_number_valid(self):
        """Test validate_input_number with valid inputs."""
        # Should not raise for valid inputs
        self.service.validate_input_number(0)
        self.service.validate_input_number(1)
        self.service.validate_input_number(2)
        self.service.validate_input_number(3)

    def test_validate_input_number_invalid_range(self):
        """Test validate_input_number with invalid ranges."""
        with pytest.raises(XPInputError, match="Invalid input number: -1"):
            self.service.validate_input_number(-1)

        with pytest.raises(XPInputError, match="Invalid input number: 4"):
            self.service.validate_input_number(4)

        with pytest.raises(XPInputError, match="Invalid input number: 10"):
            self.service.validate_input_number(10)

    def test_validate_serial_number_valid(self):
        """Test validate_serial_number with valid serial numbers."""
        # Should not raise for valid serial numbers
        self.service.validate_serial_number("0020044964")
        self.service.validate_serial_number("1234567890")
        self.service.validate_serial_number("0000000000")

    def test_validate_serial_number_invalid_length(self):
        """Test validate_serial_number with invalid lengths."""
        with pytest.raises(XPInputError, match="Invalid serial number: 123456789"):
            self.service.validate_serial_number("123456789")  # 9 digits

        with pytest.raises(XPInputError, match="Invalid serial number: 12345678901"):
            self.service.validate_serial_number("12345678901")  # 11 digits

    def test_validate_serial_number_invalid_characters(self):
        """Test validate_serial_number with non-numeric characters."""
        with pytest.raises(XPInputError, match="Invalid serial number: 002004496A"):
            self.service.validate_serial_number("002004496A")

        with pytest.raises(XPInputError, match="Invalid serial number: 0020-44964"):
            self.service.validate_serial_number("0020-44964")

    # Telegram generation tests

    @patch("xp.services.telegram_input_service.calculate_checksum")
    def test_generate_action_telegram_press(self, mock_checksum):
        """Test generate_action_telegram for PRESS action."""
        mock_checksum.return_value = "FN"

        result = self.service.generate_system_action_telegram("0020044964", 0, ActionType.PRESS)

        assert result == "<S0020044964F27D00AAFN>"
        mock_checksum.assert_called_once_with("S0020044964F27D00AA")

    @patch("xp.services.telegram_input_service.calculate_checksum")
    def test_generate_action_telegram_release(self, mock_checksum):
        """Test generate_action_telegram for RELEASE action."""
        mock_checksum.return_value = "FB"

        result = self.service.generate_system_action_telegram(
            "0020044964", 3, ActionType.RELEASE
        )

        assert result == "<S0020044964F27D03ABFB>"
        mock_checksum.assert_called_once_with("S0020044964F27D03AB")

    def test_generate_action_telegram_invalid_serial(self):
        """Test generate_action_telegram with invalid serial number."""
        with pytest.raises(XPInputError):
            self.service.generate_system_action_telegram("123", 0, ActionType.PRESS)

    def test_generate_action_telegram_invalid_input(self):
        """Test generate_action_telegram with invalid input number."""
        with pytest.raises(XPInputError):
            self.service.generate_system_action_telegram("0020044964", 5, ActionType.PRESS)

    @patch("xp.services.telegram_input_service.calculate_checksum")
    def test_generate_status_telegram(self, mock_checksum):
        """Test generate_status_telegram."""
        mock_checksum.return_value = "FJ"

        result = self.service.generate_system_status_telegram("0020044964")

        assert result == "<S0020044964F02D12FJ>"
        mock_checksum.assert_called_once_with("S0020044964F02D12")

    def test_generate_status_telegram_invalid_serial(self):
        """Test generate_status_telegram with invalid serial number."""
        with pytest.raises(XPInputError):
            self.service.generate_system_status_telegram("invalid")

    # Telegram parsing tests

    @patch.object(TelegramInputService, "validate_checksum")
    def test_parse_action_telegram_valid_press(self, mock_validate):
        """Test parse_action_telegram with valid PRESS telegram."""
        mock_validate.return_value = True

        result = self.service.parse_system_telegram("<S0020044964F27D01AAFN>")

        assert isinstance(result, InputTelegram)
        assert result.serial_number == "0020044964"
        assert result.input_number == 1
        assert result.action_type == ActionType.PRESS
        assert result.checksum == "FN"
        assert result.raw_telegram == "<S0020044964F27D01AAFN>"
        assert result.checksum_validated is True

    @patch.object(TelegramInputService, "validate_checksum")
    def test_parse_action_telegram_valid_release(self, mock_validate):
        """Test parse_action_telegram with valid RELEASE telegram."""
        mock_validate.return_value = False

        result = self.service.parse_system_telegram("<S0020044964F27D03ABFB>")

        assert result.serial_number == "0020044964"
        assert result.input_number == 3
        assert result.action_type == ActionType.RELEASE
        assert result.checksum == "FB"
        assert result.checksum_validated is False

    def test_parse_action_telegram_empty(self):
        """Test parse_action_telegram with empty string."""
        with pytest.raises(XPInputError, match="Empty telegram string"):
            self.service.parse_system_telegram("")

    def test_parse_action_telegram_invalid_format(self):
        """Test parse_action_telegram with invalid format."""
        with pytest.raises(XPInputError, match="Invalid XP24 action telegram format"):
            self.service.parse_system_telegram("<E14L00I02MAK>")  # Event telegram

    def test_parse_action_telegram_invalid_input_range(self):
        """Test parse_action_telegram with invalid input number."""
        with pytest.raises(XPInputError, match="Invalid input number: 5"):
            self.service.parse_system_telegram("<S0020044964F27D05AAFN>")

    def test_parse_action_telegram_invalid_action_code(self):
        """Test parse_action_telegram with invalid action code."""
        with pytest.raises(XPInputError, match="Invalid XP24 action telegram format: <S0020044964F27D01XXFN>"):
            self.service.parse_system_telegram("<S0020044964F27D01XXFN>")

    # Checksum validation tests

    @patch("xp.services.telegram_input_service.calculate_checksum")
    def test_validate_checksum_valid(self, mock_checksum):
        """Test validate_checksum with valid checksum."""
        mock_checksum.return_value = "FN"

        telegram = InputTelegram(checksum="FN", raw_telegram="<S0020044964F27D00AAFN>")

        result = self.service.validate_checksum(telegram)

        assert result is True
        mock_checksum.assert_called_once_with("S0020044964F27D00AA")

    @patch("xp.services.telegram_input_service.calculate_checksum")
    def test_validate_checksum_invalid(self, mock_checksum):
        """Test validate_checksum with invalid checksum."""
        mock_checksum.return_value = "FN"

        telegram = InputTelegram(checksum="XX", raw_telegram="<S0020044964F27D00AAXX>")

        result = self.service.validate_checksum(telegram)

        assert result is False

    def test_validate_checksum_malformed_telegram(self):
        """Test validate_checksum with malformed telegram."""
        telegram = InputTelegram(checksum="FN", raw_telegram="invalid_telegram")

        result = self.service.validate_checksum(telegram)

        assert result is False

    def test_validate_checksum_empty_checksum(self):
        """Test validate_checksum with empty checksum."""
        telegram = InputTelegram(checksum="", raw_telegram="<S0020044964F27D00AA>")

        result = self.service.validate_checksum(telegram)

        assert result is False

    def test_validate_checksum_wrong_length(self):
        """Test validate_checksum with wrong checksum length."""
        telegram = InputTelegram(
            checksum="F",
            raw_telegram="<S0020044964F27D00AAF>",  # Only 1 character
        )

        result = self.service.validate_checksum(telegram)

        assert result is False

    # Status parsing tests

    def test_parse_status_response_valid(self):
        """Test parse_status_response with valid response."""
        result = self.service.parse_status_response("<R0020044964F02D12xxxx1110FJ>")

        expected = {0: True, 1: True, 2: True, 3: False}
        assert result == expected

    def test_parse_status_response_all_on(self):
        """Test parse_status_response with all inputs ON."""
        result = self.service.parse_status_response("<R0020044964F02D12xxxx1111FJ>")

        expected = {0: True, 1: True, 2: True, 3: True}
        assert result == expected

    def test_parse_status_response_all_off(self):
        """Test parse_status_response with all inputs OFF."""
        result = self.service.parse_status_response("<R0020044964F02D12xxxx0000FJ>")

        expected = {0: False, 1: False, 2: False, 3: False}
        assert result == expected

    def test_parse_status_response_empty(self):
        """Test parse_status_response with empty string."""
        with pytest.raises(XPInputError, match="Empty status response telegram"):
            self.service.parse_status_response("")

    def test_parse_status_response_invalid_format(self):
        """Test parse_status_response with invalid format."""
        with pytest.raises(XPInputError, match="Invalid status response format"):
            self.service.parse_status_response("<R0020044964F18DFA>")  # ACK telegram

    def test_parse_status_response_invalid_bits_length(self):
        """Test parse_status_response with invalid status bits length."""
        with pytest.raises(XPInputError, match="Invalid status response format"):
            self.service.parse_status_response(
                "<R0020044964F02D12xxxx111FJ>"
            )  # Only 3 bits

    # Formatting tests

    def test_format_status_summary(self):
        """Test format_status_summary."""
        status = {0: True, 1: False, 2: True, 3: False}

        result = self.service.format_status_summary(status)

        expected = (
            "XP24 Input Status:\n"
            "  Input 0: ON\n"
            "  Input 1: OFF\n"
            "  Input 2: ON\n"
            "  Input 3: OFF"
        )
        assert result == expected

    def test_format_action_summary_with_validation(self):
        """Test format_action_summary with checksum validation."""
        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=1,
            action_type=ActionType.PRESS,
            checksum="FN",
            raw_telegram="<S0020044964F27D01AAFN>",
            checksum_validated=True,
        )

        result = self.service.format_action_summary(telegram)

        assert (
            "XP Input: XP Input: Press (Make) on Input 1 for device 0020044964"
            in result
        )
        assert "Raw: <S0020044964F27D01AAFN>" in result
        assert "Checksum: FN (✓)" in result

    def test_format_action_summary_without_validation(self):
        """Test format_action_summary without checksum validation."""
        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=2,
            action_type=ActionType.RELEASE,
            checksum="FB",
            raw_telegram="<S0020044964F27D02ABFB>",
            checksum_validated=None,
        )

        result = self.service.format_action_summary(telegram)

        assert "Checksum: FB" in result
        assert "✓" not in result
        assert "✗" not in result

    def test_format_action_summary_failed_validation(self):
        """Test format_action_summary with failed checksum validation."""
        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=0,
            action_type=ActionType.PRESS,
            checksum="XX",
            raw_telegram="<S0020044964F27D00AAXX>",
            checksum_validated=False,
        )

        result = self.service.format_action_summary(telegram)

        assert "Checksum: XX (✗)" in result
