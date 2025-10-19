"""Tests for LogEntry model."""

from datetime import datetime

from xp.models import EventType
from xp.models.log_entry import LogEntry
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.event_telegram import EventTelegram
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram


class TestLogEntry:
    """Test cases for LogEntry model."""

    def test_basic_log_entry(self):
        """Test creating a basic log entry."""
        timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)
        entry = LogEntry(
            timestamp=timestamp,
            direction="TX",
            raw_telegram="<S0012345008F27D00AAFN>",
            line_number=1,
        )

        assert entry.timestamp == timestamp
        assert entry.direction == "TX"
        assert entry.raw_telegram == "<S0012345008F27D00AAFN>"
        assert entry.line_number == 1
        assert entry.parsed_telegram is None
        assert entry.parse_error is None

    def test_transmitted_received_properties(self):
        """Test is_transmitted and is_received properties."""
        tx_entry = LogEntry(
            timestamp=datetime.now(),
            direction="TX",
            raw_telegram="<test>",
            line_number=1,
        )

        rx_entry = LogEntry(
            timestamp=datetime.now(),
            direction="RX",
            raw_telegram="<test>",
            line_number=2,
        )

        assert tx_entry.is_transmitted is True
        assert tx_entry.is_received is False
        assert rx_entry.is_transmitted is False
        assert rx_entry.is_received is True

    def test_telegram_type_with_event_telegram(self):
        """Test telegram_type property with event telegram."""
        event_telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
        )

        entry = LogEntry(
            timestamp=datetime.now(),
            direction="RX",
            raw_telegram="<E14L00I02MAK>",
            parsed_telegram=event_telegram,
            line_number=1,
        )

        assert entry.telegram_type == "e"
        assert entry.is_valid_parse is True

    def test_telegram_type_with_system_telegram(self):
        """Test telegram_type property with system telegram."""
        system_telegram = SystemTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0012345008F02D18FN>",
        )

        entry = LogEntry(
            timestamp=datetime.now(),
            direction="TX",
            raw_telegram="<S0012345008F02D18FN>",
            parsed_telegram=system_telegram,
            line_number=1,
        )

        assert entry.telegram_type == "s"
        assert entry.is_valid_parse is True

    def test_telegram_type_with_reply_telegram(self):
        """Test telegram_type property with reply telegram."""
        reply_telegram = ReplyTelegram(
            serial_number="0012345008",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0012345008F02D18+26,0§CIL>",
        )

        entry = LogEntry(
            timestamp=datetime.now(),
            direction="RX",
            raw_telegram="<R0012345008F02D18+26,0§CIL>",
            parsed_telegram=reply_telegram,
            line_number=1,
        )

        assert entry.telegram_type == "r"
        assert entry.is_valid_parse is True

    def test_telegram_type_unknown(self):
        """Test telegram_type property with no parsed telegram."""
        entry = LogEntry(
            timestamp=datetime.now(),
            direction="TX",
            raw_telegram="<invalid>",
            line_number=1,
        )

        assert entry.telegram_type == "unknown"
        assert entry.is_valid_parse is False

    def test_parse_error_handling(self):
        """Test log entry with parse error."""
        entry = LogEntry(
            timestamp=datetime.now(),
            direction="RX",
            raw_telegram="<malformed>",
            parse_error="Invalid telegram format",
            line_number=1,
        )

        assert entry.is_valid_parse is False
        assert entry.parse_error == "Invalid telegram format"
        assert entry.telegram_type == "unknown"

    def test_checksum_validated_property(self):
        """Test checksum_validated property."""
        # Test with event telegram that has checksum validation
        event_telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
            checksum_validated=True,
        )

        entry = LogEntry(
            timestamp=datetime.now(),
            direction="RX",
            raw_telegram="<E14L00I02MAK>",
            parsed_telegram=event_telegram,
            line_number=1,
        )

        assert entry.checksum_validated is True

        # Test with invalid checksum
        event_telegram.checksum_validated = False
        checksum_result = entry.checksum_validated
        assert checksum_result is False

    def test_to_dict(self):
        """Test to_dict serialization."""
        timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)
        event_telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
            checksum_validated=True,
        )

        result = LogEntry(
            timestamp=timestamp,
            direction="RX",
            raw_telegram="<E14L00I02MAK>",
            parsed_telegram=event_telegram,
            line_number=1,
        ).to_dict()

        expected = {
            "line_number": 1,
            "timestamp": "22:44:20.352",
            "direction": "RX",
            "raw_telegram": "<E14L00I02MAK>",
            "telegram_type": "e",
            "is_valid_parse": True,
            "parse_error": None,
            "parsed": event_telegram.to_dict(),
            "checksum_validated": True,
        }

        assert result == expected

    def test_to_dict_with_error(self):
        """Test to_dict with parse error."""
        timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)
        result = LogEntry(
            timestamp=timestamp,
            direction="TX",
            raw_telegram="<invalid>",
            parse_error="Invalid format",
            line_number=5,
        ).to_dict()

        expected = {
            "line_number": 5,
            "timestamp": "22:44:20.352",
            "direction": "TX",
            "raw_telegram": "<invalid>",
            "telegram_type": "unknown",
            "is_valid_parse": False,
            "parse_error": "Invalid format",
        }

        assert result == expected

    def test_str_representation(self):
        """Test string representation."""
        timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)
        event_telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
            checksum_validated=True,
        )

        entry = LogEntry(
            timestamp=timestamp,
            direction="RX",
            raw_telegram="<E14L00I02MAK>",
            parsed_telegram=event_telegram,
            line_number=1,
        )

        result = str(entry)
        expected = "[  1] 22:44:20,352 [RX] <E14L00I02MAK> ✓ (✓)"
        assert result == expected

    def test_str_representation_with_error(self):
        """Test string representation with parse error."""
        timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)
        entry = LogEntry(
            timestamp=timestamp,
            direction="TX",
            raw_telegram="<invalid>",
            parse_error="Invalid format",
            line_number=10,
        )

        result = str(entry)
        expected = "[ 10] 22:44:20,352 [TX] <invalid> ✗"
        assert result == expected

    def test_str_representation_invalid_checksum(self):
        """Test string representation with invalid checksum."""
        timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)
        event_telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="XX",
            raw_telegram="<E14L00I02MXX>",
            checksum_validated=False,
        )

        entry = LogEntry(
            timestamp=timestamp,
            direction="RX",
            raw_telegram="<E14L00I02MXX>",
            parsed_telegram=event_telegram,
            line_number=2,
        )

        result = str(entry)
        expected = "[  2] 22:44:20,352 [RX] <E14L00I02MXX> ✓ (✗)"
        assert result == expected
