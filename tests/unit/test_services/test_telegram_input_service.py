"""Unit tests for telegram input service."""

import pytest

from xp.models.telegram.output_telegram import OutputTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.services.telegram.telegram_output_service import (
    TelegramOutputService,
    XPOutputError,
)
from xp.services.telegram.telegram_service import TelegramService


class TestTelegramInputServiceAckNak:
    """Test cases for parse_ack_nak_telegram method in TelegramInputService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramOutputService(telegram_service=TelegramService())

    def test_parse_valid_ack_telegram(self):
        """Test parsing a valid ACK telegram."""
        raw = "<R0012345003F18DFF>"
        result = self.service.parse_reply_telegram(raw)

        assert isinstance(result, OutputTelegram)
        assert result.serial_number == "0012345003"
        assert result.system_function == SystemFunction.ACK
        assert result.checksum == "FF"
        assert result.raw_telegram == raw
        assert result.timestamp is not None
        assert (
            result.output_number is None
        )  # ACK/NAK telegrams don't have input numbers
        assert result.action_type is None  # ACK/NAK telegrams don't have action types

    def test_parse_valid_nak_telegram(self):
        """Test parsing a valid NAK telegram."""
        raw = "<R0012345003F19DAB>"
        result = self.service.parse_reply_telegram(raw)

        assert isinstance(result, OutputTelegram)
        assert result.serial_number == "0012345003"
        assert result.system_function == SystemFunction.NAK
        assert result.checksum == "AB"
        assert result.raw_telegram == raw
        assert result.timestamp is not None

    def test_parse_ack_nak_telegram_different_serial_numbers(self):
        """Test parsing ACK/NAK telegrams with different serial numbers."""
        # Test different serial number
        raw = "<R1234567890F18D12>"
        result = self.service.parse_reply_telegram(raw)
        assert result.serial_number == "1234567890"
        assert result.system_function == SystemFunction.ACK

        # Test another serial number with NAK
        raw = "<R9876543210F19D34>"
        result = self.service.parse_reply_telegram(raw)
        assert result.serial_number == "9876543210"
        assert result.system_function == SystemFunction.NAK

    def test_parse_ack_nak_telegram_different_checksums(self):
        """Test parsing ACK/NAK telegrams with different checksums."""
        # Test with alphanumeric checksum
        raw = "<R0012345003F18DA1>"
        result = self.service.parse_reply_telegram(raw)
        assert result.checksum == "A1"

        # Test with numeric checksum
        raw = "<R0012345003F19D99>"
        result = self.service.parse_reply_telegram(raw)
        assert result.checksum == "99"

        # Test with alpha checksum
        raw = "<R0012345003F18DAZ>"
        result = self.service.parse_reply_telegram(raw)
        assert result.checksum == "AZ"

    def test_parse_empty_telegram_raises_error(self):
        """Test that empty telegram raises XPInputError."""
        with pytest.raises(XPOutputError, match="Empty telegram string"):
            self.service.parse_reply_telegram("")

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises XPInputError."""
        invalid_telegrams = [
            "S0012345003F18DFF>",  # Missing opening bracket
            "<R0012345003F18DFF",  # Missing closing bracket
            "<S0012345003F18DFF>",  # Wrong prefix (S instead of R)
            "<R002004279F18DFF>",  # Serial number too short
            "<R00123450030F18DFF>",  # Serial number too long
            "<R0012345003F8DFF>",  # Function code too short
            "<R0012345003F180DFF>",  # Function code too long
            "<R0012345003F17DFF>",  # Invalid function code (17)
            "<R0012345003F20DFF>",  # Invalid function code (20)
            "<R0012345003F18DF>",  # Checksum too short
            "<R0012345003F18DFFF>",  # Checksum too long
            "<R0012345003F18D>",  # Missing checksum
        ]

        for invalid in invalid_telegrams:
            with pytest.raises(
                XPOutputError, match="Invalid XP24 response telegram format"
            ):
                print(f"Telegram {invalid}")
                self.service.parse_reply_telegram(invalid)

    def test_parse_invalid_function_code_raises_error(self):
        """Test that invalid function codes raise XPInputError."""
        # Valid format but invalid function codes (these will fail at regex level)
        invalid_function_codes = ["17", "20", "01", "02", "99", "XX"]

        for func_code in invalid_function_codes:
            raw = f"<R0012345003F{func_code}DFF>"
            with pytest.raises(
                XPOutputError, match="Invalid XP24 response telegram format"
            ):
                self.service.parse_reply_telegram(raw)

    def test_parse_with_whitespace(self):
        """Test parsing telegram with surrounding whitespace."""
        raw = "  <R0012345003F18DFF>  "
        result = self.service.parse_reply_telegram(raw)

        assert result.serial_number == "0012345003"
        assert result.system_function == SystemFunction.ACK
        assert result.raw_telegram == raw

    def test_parse_ack_nak_telegram_checksum_validation(self):
        """Test that checksum validation is performed."""
        # Create a telegram and verify checksum validation is called
        raw = "<R0012345003F18DFF>"
        result = self.service.parse_reply_telegram(raw)

        # The checksum_validated property should be set
        assert result.checksum_validated is not None
        assert isinstance(result.checksum_validated, bool)

    def test_parse_ack_nak_telegram_case_sensitivity(self):
        """Test that parsing only accepts uppercase checksums."""
        # The regex pattern expects uppercase checksums [A-Z0-9]
        raw = "<R0012345003F18Dff>"  # lowercase checksum should fail
        with pytest.raises(
            XPOutputError, match="Invalid XP24 response telegram format"
        ):
            self.service.parse_reply_telegram(raw)

    def test_parse_ack_nak_telegram_system_function_validation(self):
        """Test that only ACK (18) and NAK (19) function codes are accepted."""
        # Test ACK (18)
        raw = "<R0012345003F18DFF>"
        result = self.service.parse_reply_telegram(raw)
        assert result.system_function == SystemFunction.ACK

        # Test NAK (19)
        raw = "<R0012345003F19DFF>"
        result = self.service.parse_reply_telegram(raw)
        assert result.system_function == SystemFunction.NAK

    def test_parse_ack_nak_telegram_boundary_values(self):
        """Test parsing with boundary values."""
        # Test minimum serial number (all zeros)
        raw = "<R0000000000F18DFF>"
        result = self.service.parse_reply_telegram(raw)
        assert result.serial_number == "0000000000"

        # Test maximum serial number (all nines)
        raw = "<R9999999999F19DFF>"
        result = self.service.parse_reply_telegram(raw)
        assert result.serial_number == "9999999999"

    def test_parse_ack_nak_telegram_unknown_system_function(self):
        """Test that unknown system function codes are handled properly."""
        # Mock the SystemFunction.from_code to return None for unknown codes
        original_from_code = SystemFunction.from_code
        SystemFunction.from_code = (
            lambda code: None
        )  # This will cause the method to raise XPInputError

        try:
            raw = "<R0012345003F18DFF>"
            with pytest.raises(XPOutputError, match="Unknown system_function"):
                self.service.parse_reply_telegram(raw)
        finally:
            # Restore original method
            SystemFunction.from_code = original_from_code

    def test_output_telegram_properties_for_ack_nak(self):
        """Test that InputTelegram properties work correctly for ACK/NAK telegrams."""
        raw = "<R0012345003F18DFF>"
        result = self.service.parse_reply_telegram(raw)

        # Test that ACK/NAK telegrams have None for input-specific properties
        assert result.output_number is None
        assert result.action_type is None

        # Test that system_function is properly set
        assert result.system_function == SystemFunction.ACK

        # Test basic telegram properties
        assert result.serial_number == "0012345003"
        assert result.checksum == "FF"
        assert result.raw_telegram == raw
