"""Unit tests for TelegramOutputService.format_output_state method."""

from xp.services.telegram.telegram_output_service import TelegramOutputService


class TestFormatOutputState:
    """Test cases for format_output_state static method."""

    def test_format_xxxx0101(self):
        """Test format_output_state with 'xxxx0101'."""
        result = TelegramOutputService.format_output_state("xxxx0101")
        assert result == "1 0 1 0"

    def test_format_xxxx1110(self):
        """Test format_output_state with 'xxxx1110'."""
        result = TelegramOutputService.format_output_state("xxxx1110")
        assert result == "0 1 1 1"

    def test_format_xxxx0001(self):
        """Test format_output_state with 'xxxx0001'."""
        result = TelegramOutputService.format_output_state("xxxx0001")
        assert result == "1 0 0 0"

    def test_format_xxxx01(self):
        """Test format_output_state with 'xxxx01' (short input)."""
        result = TelegramOutputService.format_output_state("xxxx01")
        # "xxxx01" -> remove x -> "01" -> pad right -> "01  " -> invert -> "  10" -> spaces -> "    1 0"
        assert result == "    1 0"

    def test_format_xx1110(self):
        """Test format_output_state with 'xx1110'."""
        result = TelegramOutputService.format_output_state("xx1110")
        assert result == "0 1 1 1"

    def test_format_0000(self):
        """Test format_output_state with '0000' (no x)."""
        result = TelegramOutputService.format_output_state("0000")
        assert result == "0 0 0 0"

    def test_format_1111(self):
        """Test format_output_state with '1111' (no x)."""
        result = TelegramOutputService.format_output_state("1111")
        assert result == "1 1 1 1"

    def test_format_uppercase_X(self):
        """Test format_output_state with uppercase 'X'."""
        result = TelegramOutputService.format_output_state("XXXX0101")
        assert result == "1 0 1 0"

    def test_format_mixed_case(self):
        """Test format_output_state with mixed case 'xX'."""
        result = TelegramOutputService.format_output_state("xXxX1010")
        assert result == "0 1 0 1"

    def test_format_empty_string(self):
        """Test format_output_state with empty string."""
        result = TelegramOutputService.format_output_state("")
        assert result == "       "  # 4 spaces joined = 7 chars with spaces

    def test_format_single_digit(self):
        """Test format_output_state with single digit."""
        result = TelegramOutputService.format_output_state("1")
        # "1" -> pad right -> "1   " -> invert -> "   1" -> spaces -> "      1"
        assert result == "      1"

    def test_format_xxxx0053(self):
        """Test format_output_state with 'xxxx0053' - real world example."""
        result = TelegramOutputService.format_output_state("xxxx0053")
        assert result == "3 5 0 0"

    def test_format_real_telegram_1235xxxxx000(self):
        """
        Test format_output_state with real telegram data '1235xxxxx000'.

        From telegram: <R0020045057F02D1235xxxxx000BO>
        Data value: 1235xxxxx000
        Algorithm:
        1. Remove 'x': "1235000"
        2. Pad/truncate to 4 chars: "1235" (first 4 chars)
        3. Invert: "5321"
        4. Add spaces: "5 3 2 1"
        """
        result = TelegramOutputService.format_output_state("1235xxxxx000")
        assert result == "5 3 2 1"
