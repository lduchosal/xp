# Copyright (c) 2025 ldvchosal
"""Time parsing utilities for console bus logs."""

import re
from datetime import UTC, datetime, time

MAX_HOUR = 23
MAX_MINUTE = 59
MAX_SECOND = 59
MAX_MILLISECOND = 999
TIME_RANGE_PARTS = 2


class TimeParsingError(Exception):
    """Raised when time parsing fails."""


def local_now() -> datetime:
    """Return the current time as a timezone-aware datetime in the local zone.

    Returns:
        Current local time carrying its UTC offset (never naive).

    """
    return datetime.now(UTC).astimezone()


def parse_log_timestamp(
    timestamp_str: str, base_date: datetime | None = None
) -> datetime:
    """Parse timestamp from console bus log format: HH:MM:SS,mmm.

    Args:
        timestamp_str: Timestamp string (e.g., "22:44:20,352")
        base_date: Base date to use (defaults to today in the local timezone)

    Returns:
        datetime object with parsed time, carrying the timezone of
        ``base_date`` (aware in the local zone when ``base_date`` is omitted)

    Raises:
        TimeParsingError: If timestamp format is invalid

    """
    # Pattern: HH:MM:SS,mmm
    pattern = r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
    match = re.match(pattern, timestamp_str.strip())

    if not match:
        msg = f"Invalid timestamp format: {timestamp_str}"
        raise TimeParsingError(msg)

    try:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3))
        millisecond = int(match.group(4))

        # Validate ranges
        if not (0 <= hour <= MAX_HOUR):
            msg = f"Invalid hour: {hour}"
            raise TimeParsingError(msg)
        if not (0 <= minute <= MAX_MINUTE):
            msg = f"Invalid minute: {minute}"
            raise TimeParsingError(msg)
        if not (0 <= second <= MAX_SECOND):
            msg = f"Invalid second: {second}"
            raise TimeParsingError(msg)
        if not (0 <= millisecond <= MAX_MILLISECOND):
            msg = f"Invalid millisecond: {millisecond}"
            raise TimeParsingError(msg)

        # Create time object
        time_obj = time(hour, minute, second, millisecond * 1000)  # microseconds

        # Use base date or today (keeping the base date's timezone)
        effective_base = local_now() if base_date is None else base_date

        return datetime.combine(
            effective_base.date(), time_obj, tzinfo=effective_base.tzinfo
        )

    except ValueError as e:
        msg = f"Error parsing timestamp {timestamp_str}: {e}"
        raise TimeParsingError(msg) from e


def format_log_timestamp(dt: datetime) -> str:
    """Format datetime to console bus log timestamp format: HH:MM:SS,mmm.

    Args:
        dt: datetime object to format

    Returns:
        Formatted timestamp string

    """
    return dt.strftime("%H:%M:%S,%f")[:-3]  # Remove last 3 digits of microseconds


def parse_time_range(
    time_range_str: str, base_date: datetime | None = None
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
    if len(parts) != TIME_RANGE_PARTS:
        msg = f"Invalid time range format: {time_range_str}"
        raise TimeParsingError(msg)

    start_time = parse_log_timestamp(parts[0].strip(), base_date)
    end_time = parse_log_timestamp(parts[1].strip(), base_date)

    if start_time > end_time:
        msg = f"Start time {parts[0]} is after end time {parts[1]}"
        raise TimeParsingError(msg)

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
    except TimeParsingError:
        return False
    else:
        return True
