"""Time parsing utilities for console bus logs."""

import re
from datetime import datetime, time
from typing import Optional


class TimeParsingError(Exception):
    """Raised when time parsing fails."""

    pass


def parse_log_timestamp(
    timestamp_str: str, base_date: Optional[datetime] = None
) -> datetime:
    """Parse timestamp from console bus log format: HH:MM:SS,mmm.

    Args:
        timestamp_str: Timestamp string (e.g., "22:44:20,352")
        base_date: Base date to use (defaults to today)

    Returns:
        datetime object with parsed time

    Raises:
        TimeParsingError: If timestamp format is invalid
    """
    # Pattern: HH:MM:SS,mmm
    pattern = r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
    match = re.match(pattern, timestamp_str.strip())

    if not match:
        raise TimeParsingError(f"Invalid timestamp format: {timestamp_str}")

    try:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3))
        millisecond = int(match.group(4))

        # Validate ranges
        if not (0 <= hour <= 23):
            raise TimeParsingError(f"Invalid hour: {hour}")
        if not (0 <= minute <= 59):
            raise TimeParsingError(f"Invalid minute: {minute}")
        if not (0 <= second <= 59):
            raise TimeParsingError(f"Invalid second: {second}")
        if not (0 <= millisecond <= 999):
            raise TimeParsingError(f"Invalid millisecond: {millisecond}")

        # Create time object
        time_obj = time(hour, minute, second, millisecond * 1000)  # microseconds

        # Use base date or today
        if base_date is None:
            date_part = datetime.now().date()
        else:
            date_part = base_date.date()

        return datetime.combine(date_part, time_obj)

    except ValueError as e:
        raise TimeParsingError(f"Error parsing timestamp {timestamp_str}: {e}")


def format_log_timestamp(dt: datetime) -> str:
    """Format datetime to console bus log timestamp format: HH:MM:SS,mmm.

    Args:
        dt: datetime object to format

    Returns:
        Formatted timestamp string
    """
    return dt.strftime("%H:%M:%S,%f")[:-3]  # Remove last 3 digits of microseconds


def parse_time_range(
    time_range_str: str, base_date: Optional[datetime] = None
) -> tuple[datetime, datetime]:
    """Parse time range string like "22:44:20,352-22:44:25,500".

    Args:
        time_range_str: Time range string
        base_date: Base date to use

    Returns:
        Tuple of (start_time, end_time)

    Raises:
        TimeParsingError: If format is invalid
    """
    parts = time_range_str.split("-")
    if len(parts) != 2:
        raise TimeParsingError(f"Invalid time range format: {time_range_str}")

    start_time = parse_log_timestamp(parts[0].strip(), base_date)
    end_time = parse_log_timestamp(parts[1].strip(), base_date)

    if start_time > end_time:
        raise TimeParsingError(f"Start time {parts[0]} is after end time {parts[1]}")

    return start_time, end_time


def calculate_duration_ms(start_time: datetime, end_time: datetime) -> int:
    """Calculate duration between two timestamps in milliseconds.

    Args:
        start_time: Start timestamp
        end_time: End timestamp

    Returns:
        Duration in milliseconds
    """
    duration = end_time - start_time
    return int(duration.total_seconds() * 1000)


def is_valid_log_timestamp(timestamp_str: str) -> bool:
    """Check if timestamp string is valid console bus log format.

    Args:
        timestamp_str: Timestamp string to validate

    Returns:
        True if valid format, False otherwise
    """
    try:
        parse_log_timestamp(timestamp_str)
        return True
    except TimeParsingError:
        return False
