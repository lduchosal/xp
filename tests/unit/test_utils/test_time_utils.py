"""Tests for time parsing utilities."""

from datetime import datetime

import pytest

from xp.utils.time_utils import (
    TimeParsingError,
    calculate_duration_ms,
    format_log_timestamp,
    is_valid_log_timestamp,
    parse_log_timestamp,
    parse_time_range,
)


class TestTimeUtils:
    """Test cases for time parsing utilities."""

    def test_parse_log_timestamp_valid(self):
        """Test parsing valid timestamp."""
        result = parse_log_timestamp("22:44:20,352")

        # Should use today's date by default
        today = datetime.now().date()
        expected = datetime.combine(
            today, datetime.strptime("22:44:20.352", "%H:%M:%S.%f").time()
        )

        assert result == expected

    def test_parse_log_timestamp_with_base_date(self):
        """Test parsing timestamp with specific base date."""
        base_date = datetime(2023, 1, 15, 10, 30, 0)
        result = parse_log_timestamp("22:44:20,352", base_date)

        expected = datetime(2023, 1, 15, 22, 44, 20, 352000)
        assert result == expected

    def test_parse_log_timestamp_edge_cases(self):
        """Test parsing edge case timestamps."""
        # Midnight
        result = parse_log_timestamp("00:00:00,000")
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

        # End of day
        result = parse_log_timestamp("23:59:59,999")
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        assert result.microsecond == 999000

    def test_parse_log_timestamp_invalid_format(self):
        """Test parsing invalid timestamp formats."""
        invalid_formats = [
            "22:44:20",  # Missing milliseconds
            "22:44:20.352",  # Wrong separator
            "22-44-20,352",  # Wrong time separator
            "22:44,352",  # Missing seconds
            "not_a_time",  # Invalid format
            "",  # Empty string
            "25:00:00,000",  # Invalid hour
            "22:60:00,000",  # Invalid minute
            "22:44:60,000",  # Invalid second
            "22:44:20,1000",  # Invalid millisecond
        ]

        for invalid_timestamp in invalid_formats:
            with pytest.raises(TimeParsingError):
                parse_log_timestamp(invalid_timestamp)

    def test_format_log_timestamp(self):
        """Test formatting datetime to log timestamp."""
        dt = datetime(2023, 1, 1, 22, 44, 20, 352000)
        result = format_log_timestamp(dt)

        assert result == "22:44:20,352"

    def test_format_log_timestamp_edge_cases(self):
        """Test formatting edge case datetimes."""
        # Midnight
        dt = datetime(2023, 1, 1, 0, 0, 0, 0)
        assert format_log_timestamp(dt) == "00:00:00,000"

        # End of day
        dt = datetime(2023, 1, 1, 23, 59, 59, 999000)
        assert format_log_timestamp(dt) == "23:59:59,999"

        # With microseconds that need rounding
        dt = datetime(2023, 1, 1, 12, 30, 45, 123456)
        assert format_log_timestamp(dt) == "12:30:45,123"

    def test_parse_time_range_valid(self):
        """Test parsing valid time range."""
        start_time, end_time = parse_time_range("22:44:20,352-22:44:25,500")

        today = datetime.now().date()
        expected_start = datetime.combine(
            today, datetime.strptime("22:44:20.352", "%H:%M:%S.%f").time()
        )
        expected_end = datetime.combine(
            today, datetime.strptime("22:44:25.500", "%H:%M:%S.%f").time()
        )

        assert start_time == expected_start
        assert end_time == expected_end

    def test_parse_time_range_with_base_date(self):
        """Test parsing time range with base date."""
        base_date = datetime(2023, 1, 15)
        start_time, end_time = parse_time_range("10:00:00,000-11:30:15,500", base_date)

        expected_start = datetime(2023, 1, 15, 10, 0, 0, 0)
        expected_end = datetime(2023, 1, 15, 11, 30, 15, 500000)

        assert start_time == expected_start
        assert end_time == expected_end

    def test_parse_time_range_invalid_format(self):
        """Test parsing invalid time range formats."""
        invalid_ranges = [
            "22:44:20,352",  # Missing end time
            "22:44:20,352-",  # Missing end time
            "-22:44:20,352",  # Missing start time
            "22:44:20,352_22:45:00,000",  # Wrong separator
            "invalid-22:44:20,352",  # Invalid start time
            "22:44:20,352-invalid",  # Invalid end time
            "",  # Empty string
        ]

        for invalid_range in invalid_ranges:
            with pytest.raises(TimeParsingError):
                parse_time_range(invalid_range)

    def test_parse_time_range_start_after_end(self):
        """Test parsing time range where start is after end."""
        with pytest.raises(TimeParsingError, match="Start time .* is after end time"):
            parse_time_range("22:44:25,500-22:44:20,352")

    def test_calculate_duration_ms(self):
        """Test calculating duration in milliseconds."""
        start = datetime(2023, 1, 1, 22, 44, 20, 352000)
        end = datetime(2023, 1, 1, 22, 44, 25, 500000)

        duration = calculate_duration_ms(start, end)
        expected = (25 - 20) * 1000 + (500 - 352)  # 5148 ms

        assert duration == expected

    def test_calculate_duration_ms_edge_cases(self):
        """Test duration calculation edge cases."""
        # Same time
        dt = datetime(2023, 1, 1, 12, 0, 0, 0)
        assert calculate_duration_ms(dt, dt) == 0

        # One-millisecond difference
        start = datetime(2023, 1, 1, 12, 0, 0, 0)
        end = datetime(2023, 1, 1, 12, 0, 0, 1000)
        assert calculate_duration_ms(start, end) == 1

        # Cross day boundary (shouldn't happen in log files but test anyway)
        start = datetime(2023, 1, 1, 23, 59, 59, 999000)
        end = datetime(2023, 1, 2, 0, 0, 0, 1000)
        expected = 2  # 1 ms remaining in day 1 + 1 ms in day 2
        assert calculate_duration_ms(start, end) == expected

    def test_is_valid_log_timestamp(self):
        """Test timestamp validation function."""
        # Valid timestamps
        valid_timestamps = [
            "00:00:00,000",
            "12:30:45,123",
            "23:59:59,999",
            "22:44:20,352",
        ]

        for timestamp in valid_timestamps:
            assert is_valid_log_timestamp(timestamp) is True

        # Invalid timestamps
        invalid_timestamps = [
            "22:44:20",  # Missing milliseconds
            "25:00:00,000",  # Invalid hour
            "22:60:00,000",  # Invalid minute
            "22:44:60,000",  # Invalid second
            "22:44:20,1000",  # Invalid millisecond
            "not_a_time",  # Invalid format
            "",  # Empty string
        ]

        for timestamp in invalid_timestamps:
            assert is_valid_log_timestamp(timestamp) is False

    def test_round_trip_timestamp_conversion(self):
        """Test that parse -> format -> parse gives same result."""
        original_timestamps = [
            "00:00:00,000",
            "12:30:45,123",
            "23:59:59,999",
            "22:44:20,352",
        ]

        for original in original_timestamps:
            # Parse to datetime
            dt = parse_log_timestamp(original)
            # Format back to string
            formatted = format_log_timestamp(dt)
            # Should match original
            assert formatted == original

            # Parse again to verify consistency
            dt2 = parse_log_timestamp(formatted)
            assert dt == dt2
