"""Unit tests for telegram service."""

import pytest

from xp.models import EventType, InputType
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.event_telegram import EventTelegram
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService


class TestTelegramService:
    """Test cases for TelegramService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramService()

    def test_parse_valid_button_press_telegram(self):
        """Test parsing a valid button press telegram."""
        raw = "<E14L00I02MAK>"
        result = self.service.parse_event_telegram(raw)

        assert result.module_type == 14
        assert result.link_number == 0
        assert result.input_number == 2
        assert result.event_type == EventType.BUTTON_PRESS
        assert result.checksum == "AK"
        assert result.raw_telegram == raw
        assert result.is_button_press is True
        assert result.input_type == InputType.PUSH_BUTTON

    def test_parse_valid_button_release_telegram(self):
        """Test parsing a valid button release telegram."""
        raw = "<E14L01I03BB1>"
        result = self.service.parse_event_telegram(raw)

        assert result.module_type == 14
        assert result.link_number == 1
        assert result.input_number == 3
        assert result.event_type == EventType.BUTTON_RELEASE
        assert result.checksum == "B1"
        assert result.is_button_release is True

    def test_parse_event_telegram_with_single_digit_module(self):
        """Test parsing telegram with single digit module type."""
        raw = "<E5L00I02MAK>"
        result = self.service.parse_event_telegram(raw)

        assert result.module_type == 5

    def test_parse_event_telegram_ir_remote_input(self):
        """Test parsing telegram with IR remote input."""
        raw = "<E14L00I25MXX>"
        result = self.service.parse_event_telegram(raw)

        assert result.input_number == 25
        assert result.input_type == InputType.IR_REMOTE

    def test_parse_event_telegram_proximity_sensor(self):
        """Test parsing telegram with proximity sensor input."""
        raw = "<E14L00I90MXX>"
        result = self.service.parse_event_telegram(raw)

        assert result.input_number == 90
        assert result.input_type == InputType.PROXIMITY_SENSOR

    def test_parse_empty_telegram_raises_error(self):
        """Test that empty telegram raises TelegramParsingError."""
        with pytest.raises(TelegramParsingError, match="Empty telegram string"):
            self.service.parse_event_telegram("")

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises TelegramParsingError."""
        invalid_telegrams = [
            "E14L00I02MAK>",  # Missing opening bracket
            "<E14L00I02MAK",  # Missing closing bracket
            "<X14L00I02MAK>",  # Wrong prefix
            "<E14X00I02MAK>",  # Invalid link format
            "<E14L00X02MAK>",  # Invalid input format
            "<E14L00I02XAK>",  # Invalid event type
            "<E14L00I02MA>",  # Short checksum
            "<E14L00I02MAKX>",  # Long checksum
        ]

        for invalid in invalid_telegrams:
            with pytest.raises(TelegramParsingError, match="Invalid telegram format"):
                self.service.parse_event_telegram(invalid)

    def test_parse_out_of_range_values_raises_error(self):
        """Test that out-of-range values raise TelegramParsingError."""
        # Input number out of range
        with pytest.raises(
            TelegramParsingError, match="Invalid telegram format: <E14L00IAAMAK>"
        ):
            self.service.parse_event_telegram("<E14L00IAAMAK>")

        # Test invalid formats that don't match regex
        with pytest.raises(TelegramParsingError, match="Invalid telegram format"):
            self.service.parse_event_telegram("<E14L100I02MAK>")  # 3-digit link number

    def test_parse_invalid_event_type_raises_error(self):
        """Test that invalid event type raises TelegramParsingError."""
        with pytest.raises(TelegramParsingError, match="Invalid telegram format"):
            self.service.parse_event_telegram("<E14L00I02XAK>")

    def test_parse_event_telegram_test_event_type_validation(self):
        """Test event type validation logic separately."""
        # The regex pattern only allows M or B, so let's test this more specifically
        # by temporarily modifying the service to test the enum validation
        service = TelegramService()
        # This tests that only M and B are allowed in the regex itself
        valid_m = service.parse_event_telegram("<E14L00I02MAK>")
        assert valid_m.event_type == EventType.BUTTON_PRESS

        valid_b = service.parse_event_telegram("<E14L00I02BAK>")
        assert valid_b.event_type == EventType.BUTTON_RELEASE

    def test_parse_with_whitespace(self):
        """Test parsing telegram with surrounding whitespace."""
        raw = "  <E14L00I02MAK>  "
        result = self.service.parse_event_telegram(raw)

        assert result.module_type == 14
        assert result.raw_telegram == raw

    def test_validate_checksum_valid(self):
        """Test checksum validation for valid checksum."""
        telegram = self.service.parse_event_telegram("<E14L00I02MAK>")
        result = self.service.validate_checksum(telegram)

        assert result is True  # AK is valid (2 alphanumeric chars)

    def test_validate_checksum_invalid_length(self):
        """Test checksum validation for invalid length."""
        # This would be caught during parsing, but test the validation logic
        telegram = self.service.parse_event_telegram("<E14L00I02MAK>")
        telegram.checksum = "A"  # Manually set invalid checksum

        result = self.service.validate_checksum(telegram)
        assert result is False

    def test_format_telegram_summary(self):
        """Test formatting telegram for human-readable output."""
        telegram = self.service.parse_event_telegram("<E14L00I02MAK>")
        summary = self.service.format_event_telegram_summary(telegram)

        # Updated to include module name
        assert (
            "Event: XP2606 (Type 14) Link 00 Input 02 (push_button) pressed" in summary
        )
        assert "Raw: <E14L00I02MAK>" in summary
        assert "Timestamp:" in summary
        assert "Checksum: AK" in summary

    def test_parse_event_telegram_non_numeric_module_raises_error(self):
        """Test that non-numeric module type raises error."""
        # This should be caught by regex, but test edge case
        with pytest.raises(TelegramParsingError, match="Invalid telegram format"):
            self.service.parse_event_telegram("<EabL00I02MAK>")

    def test_parse_event_telegram_boundary_values(self):
        """Test parsing telegrams with boundary values."""
        # Test maximum valid values
        telegram = self.service.parse_event_telegram("<E99L99I90M00>")
        assert telegram.module_type == 99
        assert telegram.link_number == 99
        assert telegram.input_number == 90

        # Test minimum valid values
        telegram = self.service.parse_event_telegram("<E1L00I00MAK>")
        assert telegram.module_type == 1
        assert telegram.link_number == 0
        assert telegram.input_number == 0

    def test_validate_checksum_invalid_chars(self):
        """Test checksum validation with invalid characters."""
        telegram = self.service.parse_event_telegram("<E14L00I02MAK>")
        telegram.checksum = "A!"  # Invalid characters
        result = self.service.validate_checksum(telegram)
        assert result is False


class TestSystemTelegramParsing:
    """Test cases for system telegram parsing in TelegramService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramService()

    def test_parse_valid_system_telegram(self):
        """Test parsing a valid system telegram."""
        raw = "<S0020012521F02D18FN>"
        result = self.service.parse_system_telegram(raw)

        assert isinstance(result, SystemTelegram)
        assert result.serial_number == "0020012521"
        assert result.system_function == SystemFunction.READ_DATAPOINT
        assert result.datapoint_type == DataPointType.TEMPERATURE
        assert result.checksum == "FN"
        assert result.raw_telegram == raw
        assert result.timestamp is not None

    def test_parse_system_telegram_different_functions(self):
        """Test parsing system telegrams with different functions."""
        # Update firmware function
        raw = "<S0020012521F01D18FN>"
        result = self.service.parse_system_telegram(raw)
        assert result.system_function == SystemFunction.DISCOVERY

        # Read config function
        raw = "<S0020012521F03D18FN>"
        result = self.service.parse_system_telegram(raw)
        assert result.system_function == SystemFunction.READ_CONFIG

    def test_parse_system_telegram_different_data_points(self):
        """Test parsing system telegrams with different data points."""
        # Humidity data point
        raw = "<S0020012521F02D19FN>"
        result = self.service.parse_system_telegram(raw)
        assert result.datapoint_type == DataPointType.SW_TOP_VERSION

        # VOLTAGE data point
        raw = "<S0020012521F02D20FN>"
        result = self.service.parse_system_telegram(raw)
        assert result.datapoint_type == DataPointType.VOLTAGE

        # Status data point
        raw = "<S0020012521F02D00FN>"
        result = self.service.parse_system_telegram(raw)
        assert result.datapoint_type == DataPointType.MODULE_TYPE

    def test_parse_system_telegram_empty_string(self):
        """Test parsing empty string raises error."""
        with pytest.raises(TelegramParsingError, match="Empty telegram string"):
            self.service.parse_system_telegram("")

    def test_parse_system_telegram_invalid_format(self):
        """Test parsing invalid format raises error."""
        with pytest.raises(
            TelegramParsingError, match="Invalid system telegram format"
        ):
            self.service.parse_system_telegram(
                "<S002001252F02D18FN>"
            )  # Wrong serial number length

        with pytest.raises(
            TelegramParsingError, match="Invalid system telegram format"
        ):
            self.service.parse_system_telegram(
                "<S0020012521F2D18FN>"
            )  # Wrong function format

        with pytest.raises(
            TelegramParsingError, match="Invalid system telegram format"
        ):
            self.service.parse_system_telegram(
                "<S0020012521F02D8FN>"
            )  # Wrong data point format

    def test_parse_system_telegram_unknown_function(self):
        """Test parsing system telegram with unknown function code."""
        with pytest.raises(
            TelegramParsingError, match="Unknown system function code: 99"
        ):
            self.service.parse_system_telegram("<S0020012521F99D18FN>")

    def test_parse_system_telegram_with_whitespace(self):
        """Test parsing system telegram with surrounding whitespace."""
        raw = "  <S0020012521F02D18FN>  "
        result = self.service.parse_system_telegram(raw)

        assert result.serial_number == "0020012521"
        assert result.raw_telegram == raw

    def test_format_system_telegram_summary(self):
        """Test formatting system telegram for human-readable output."""
        telegram = self.service.parse_system_telegram("<S0020012521F02D18FN>")
        summary = self.service.format_system_telegram_summary(telegram)

        assert "Raw: <S0020012521F02D18FN>" in summary
        assert "Timestamp:" in summary
        assert "Checksum: FN" in summary


class TestReplyTelegramParsing:
    """Test cases for reply telegram parsing in TelegramService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramService()

    def test_parse_valid_reply_telegram(self):
        """Test parsing a valid reply telegram."""
        raw = "<R0020012521F02D18+26,0§CIL>"
        result = self.service.parse_reply_telegram(raw)

        assert isinstance(result, ReplyTelegram)
        assert result.serial_number == "0020012521"
        assert result.system_function == SystemFunction.READ_DATAPOINT
        assert result.datapoint_type == DataPointType.TEMPERATURE
        assert result.data_value == "+26,0§C"
        assert result.checksum == "IL"
        assert result.raw_telegram == raw
        assert result.timestamp is not None

    def test_parse_reply_telegram_different_values(self):
        """Test parsing reply telegrams with different data values."""
        # Humidity reply
        raw = "<R0020012521F02D19+65,5§HIL>"
        result = self.service.parse_reply_telegram(raw)
        assert result.datapoint_type == DataPointType.SW_TOP_VERSION
        assert result.data_value == "+65,5§H"

        # VOLTAGE reply
        raw = "<R0020012521F02D20+12,5§VIL>"
        result = self.service.parse_reply_telegram(raw)
        assert result.datapoint_type == DataPointType.VOLTAGE
        assert result.data_value == "+12,5§V"

        # Status reply
        raw = "<R0020012521F02D00OKIL>"
        result = self.service.parse_reply_telegram(raw)
        assert result.datapoint_type == DataPointType.MODULE_TYPE
        assert result.data_value == "OK"

    def test_parse_reply_telegram_complex_data_values(self):
        """Test parsing reply telegrams with complex data values."""
        # Negative temperature
        raw = "<R0020012521F02D18-15,2§CIL>"
        result = self.service.parse_reply_telegram(raw)
        assert result.data_value == "-15,2§C"

        # Multi-character status
        raw = "<R0020012521F02D00ERROR_123IL>"
        result = self.service.parse_reply_telegram(raw)
        assert result.data_value == "ERROR_123"

    def test_parse_reply_telegram_empty_string(self):
        """Test parsing empty string raises error."""
        with pytest.raises(TelegramParsingError, match="Empty telegram string"):
            self.service.parse_reply_telegram("")

    def test_parse_reply_telegram_invalid_format(self):
        """Test parsing invalid format raises error."""
        with pytest.raises(TelegramParsingError, match="Invalid reply telegram format"):
            self.service.parse_reply_telegram(
                "<R002001252F02D18+26,0§CIL>"
            )  # Wrong serial number length

        with pytest.raises(TelegramParsingError, match="Invalid reply telegram format"):
            self.service.parse_reply_telegram(
                "<R0020012521F2D18+26,0§CIL>"
            )  # Wrong function format

    def test_parse_reply_telegram_unknown_function(self):
        """Test parsing reply telegram with unknown function code."""
        with pytest.raises(
            TelegramParsingError, match="Unknown system function code: 99"
        ):
            self.service.parse_reply_telegram("<R0020012521F99D18+26,0§CIL>")

    def test_parse_reply_telegram_with_whitespace(self):
        """Test parsing reply telegram with surrounding whitespace."""
        raw = "  <R0020012521F02D18+26,0§CIL>  "
        result = self.service.parse_reply_telegram(raw)

        assert result.serial_number == "0020012521"
        assert result.raw_telegram == raw

    def test_format_reply_telegram_summary(self):
        """Test formatting reply telegram for human-readable output."""
        telegram = self.service.parse_reply_telegram("<R0020012521F02D18+26,0§CIL>")
        summary = self.service.format_reply_telegram_summary(telegram)

        assert "Reply Telegram: READ_DATAPOINT" in summary
        assert "for TEMPERATURE = 26.0" in summary
        assert "from device 0020012521" in summary
        assert "Data: 26.0°C" in summary
        assert "Raw: <R0020012521F02D18+26,0§CIL>" in summary
        assert "Timestamp:" in summary
        assert "Checksum: IL" in summary

    def test_parse_actiontable_reply_telegram(self):
        """Test parsing an actiontable reply telegram (F17).

        This tests a real actiontable telegram received from a module.
        The F17 function code indicates ACTIONTABLE data response.
        """
        raw = "<R0020042796F17DAAAADDBAAABAAADDBAAABBAADDBAAABCAADDBAAIAIAADDBAAIAJAA>"
        result = self.service.parse_reply_telegram(raw)

        assert isinstance(result, ReplyTelegram)
        assert result.serial_number == "0020042796"
        assert result.system_function == SystemFunction.ACTIONTABLE
        assert result.data == "AA"
        assert result.data_value == "AADDBAAABAAADDBAAABBAADDBAAABCAADDBAAIAIAADDBAAIAJ"
        assert result.checksum == "AA"
        assert not result.checksum_validated
        assert result.raw_telegram == raw
        assert result.timestamp is not None


class TestAutoDetectTelegramParsing:
    """Test cases for auto-detect telegram parsing in TelegramService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TelegramService()

    def test_parse_telegram_event(self):
        """Test auto-parsing event telegram."""
        raw = "<E14L00I02MAK>"
        result = self.service.parse_telegram(raw)

        assert isinstance(result, EventTelegram)
        assert result.module_type == 14
        assert hasattr(result, "event_type")

    def test_parse_telegram_system(self):
        """Test auto-parsing system telegram."""
        raw = "<S0020012521F02D18FN>"
        result = self.service.parse_telegram(raw)

        assert isinstance(result, SystemTelegram)
        assert result.serial_number == "0020012521"
        assert not hasattr(result, "data_value")

    def test_parse_telegram_reply(self):
        """Test auto-parsing reply telegram."""
        raw = "<R0020012521F02D18+26,0§CIL>"
        result = self.service.parse_telegram(raw)

        assert isinstance(result, ReplyTelegram)
        assert result.serial_number == "0020012521"
        assert hasattr(result, "data_value")
        assert result.data_value == "+26,0§C"

    def test_parse_telegram_empty_string(self):
        """Test parsing empty string raises error."""
        with pytest.raises(TelegramParsingError, match="Empty telegram string"):
            self.service.parse_telegram("")

    def test_parse_telegram_unknown_type(self):
        """Test parsing unknown telegram type raises error."""
        with pytest.raises(TelegramParsingError, match="Unknown telegram type code: X"):
            self.service.parse_telegram("<X0020012521F02D18+26,0§CIL>")

    def test_parse_telegram_invalid_format(self):
        """Test parsing invalid format raises error for appropriate type."""
        # This should try to parse as system telegram and fail
        with pytest.raises(
            TelegramParsingError, match="Invalid system telegram format"
        ):
            self.service.parse_telegram("<S002001252F02D18FN>")

        # This should try to parse as reply telegram and fail
        with pytest.raises(TelegramParsingError, match="Invalid reply telegram format"):
            self.service.parse_telegram("<R002001252F02D18+26,0§CIL>")

        # This should try to parse as event telegram and fail
        with pytest.raises(TelegramParsingError, match="Invalid telegram format"):
            self.service.parse_telegram("<E14L100I02MAK>")

    def test_parse_telegram_short_string(self):
        """Test parsing very short string raises error."""
        with pytest.raises(TelegramParsingError, match="Unknown telegram type"):
            self.service.parse_telegram("<")

    @pytest.mark.parametrize(
        "raw_telegram,expected_type",
        [
            ("<E14L00I02MAK>", EventTelegram),
            ("<S0020012521F02D18FN>", SystemTelegram),
            ("<R0020012521F02D18+26,0§CIL>", ReplyTelegram),
        ],
    )
    def test_parse_telegram_type_detection(self, raw_telegram, expected_type):
        """Test that parse_telegram correctly detects telegram types."""
        result = self.service.parse_telegram(raw_telegram)
        assert isinstance(result, expected_type)
