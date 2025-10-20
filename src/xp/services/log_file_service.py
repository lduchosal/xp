"""Log file parsing service for console bus communication logs."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from xp.models.log_entry import LogEntry
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService
from xp.utils.time_utils import (
    TimeParsingError,
    calculate_duration_ms,
    parse_log_timestamp,
)


class LogFileParsingError(Exception):
    """Raised when log file parsing fails."""

    pass


class LogFileService:
    """
    Service for parsing console bus log files.

    Handles parsing of log files containing timestamped telegram transmissions
    and receptions with automatic telegram parsing and validation.

    Attributes:
        telegram_service: Telegram service for parsing telegrams.
        LOG_LINE_PATTERN: Regex pattern for log line format.
    """

    # Regex pattern for log line format: HH:MM:SS,mmm [TX/RX] <telegram>
    LOG_LINE_PATTERN = re.compile(
        r"^(\d{2}:\d{2}:\d{2},\d{3})\s+\[([TR]X)\]\s+(<[^>]+>)\s*$"
    )

    def __init__(self, telegram_service: TelegramService):
        """Initialize the log file service.

        Args:
            telegram_service: Telegram service for parsing telegrams.
        """
        self.telegram_service = telegram_service

    def parse_log_file(
        self, file_path: str, base_date: Optional[datetime] = None
    ) -> List[LogEntry]:
        """Parse a console bus log file into LogEntry objects.

        Args:
            file_path: Path to the log file.
            base_date: Base date for timestamps (defaults to today).

        Returns:
            List of parsed LogEntry objects.

        Raises:
            LogFileParsingError: If file cannot be read or parsed.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise LogFileParsingError(f"Log file not found: {file_path}")

            if not path.is_file():
                raise LogFileParsingError(f"Path is not a file: {file_path}")

            with Path(path).open("r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            return self.parse_log_lines(lines, base_date)

        except IOError as e:
            raise LogFileParsingError(f"Error reading log file {file_path}: {e}")

    def parse_log_lines(
        self, lines: List[str], base_date: Optional[datetime] = None
    ) -> List[LogEntry]:
        """Parse log lines into LogEntry objects.

        Args:
            lines: List of log lines to parse.
            base_date: Base date for timestamps.

        Returns:
            List of parsed LogEntry objects.
        """
        entries = []

        for line_number, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            try:
                entry = self._parse_log_line(line, line_number, base_date)
                if entry:
                    entries.append(entry)
            except Exception as e:
                # Create entry with parse error for malformed lines
                entry = LogEntry(
                    timestamp=base_date or datetime.now(),
                    direction="UNKNOWN",
                    raw_telegram=line,
                    parse_error=f"Line parsing failed: {e}",
                    line_number=line_number,
                )
                entries.append(entry)

        return entries

    def _parse_log_line(
        self, line: str, line_number: int, base_date: Optional[datetime] = None
    ) -> Optional[LogEntry]:
        """Parse a single log line into a LogEntry.

        Args:
            line: Log line to parse.
            line_number: Line number in the file.
            base_date: Base date for timestamp.

        Returns:
            LogEntry object or None if line format is invalid.
        """
        match = self.LOG_LINE_PATTERN.match(line)
        if not match:
            raise LogFileParsingError(f"Invalid log line format: {line}")

        timestamp_str = match.group(1)
        direction = match.group(2)
        telegram_str = match.group(3)

        # Parse timestamp
        try:
            timestamp = parse_log_timestamp(timestamp_str, base_date)
        except TimeParsingError as e:
            raise LogFileParsingError(f"Invalid timestamp in line {line_number}: {e}")

        # Create initial log entry
        entry = LogEntry(
            timestamp=timestamp,
            direction=direction,
            raw_telegram=telegram_str,
            line_number=line_number,
        )

        # Try to parse the telegram
        try:
            parsed_telegram = self.telegram_service.parse_telegram(telegram_str)
            entry.parsed_telegram = parsed_telegram
        except TelegramParsingError as e:
            entry.parse_error = str(e)

        return entry

    def validate_log_format(self, file_path: str) -> bool:
        """Validate that a file follows the expected log format.

        Args:
            file_path: Path to the log file.

        Returns:
            True if format is valid, False otherwise.
        """
        try:
            entries = self.parse_log_file(file_path)
            # Check if at least some entries parsed successfully
            valid_entries = [e for e in entries if e.is_valid_parse]
            return len(valid_entries) > 0
        except LogFileParsingError:
            return False

    def extract_telegrams(self, file_path: str) -> List[str]:
        """Extract all telegram strings from a log file.

        Args:
            file_path: Path to the log file.

        Returns:
            List of telegram strings.
        """
        entries = self.parse_log_file(file_path)
        return [entry.raw_telegram for entry in entries]

    @staticmethod
    def get_file_statistics(entries: List[LogEntry]) -> Dict[str, Any]:
        """Generate statistics for a list of log entries.

        Args:
            entries: List of LogEntry objects.

        Returns:
            Dictionary containing statistics.
        """
        if not entries:
            return {"total_entries": 0}

        # Basic counts
        total_entries = len(entries)
        valid_parses = len([e for e in entries if e.is_valid_parse])
        parse_errors = total_entries - valid_parses

        # Direction counts
        tx_count = len([e for e in entries if e.direction == "TX"])
        rx_count = len([e for e in entries if e.direction == "RX"])

        # Type counts
        event_count = len([e for e in entries if e.telegram_type == "E"])
        system_count = len([e for e in entries if e.telegram_type == "S"])
        reply_count = len([e for e in entries if e.telegram_type == "R"])
        unknown_count = len([e for e in entries if e.telegram_type == "unknown"])

        # Checksum validation
        validated_entries = [e for e in entries if e.checksum_validated is not None]
        valid_checksums = len([e for e in validated_entries if e.checksum_validated])
        invalid_checksums = len(validated_entries) - valid_checksums

        # Time range
        timestamps = [e.timestamp for e in entries]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None
        duration_ms = (
            calculate_duration_ms(start_time, end_time)
            if start_time and end_time
            else 0
        )

        # Device analysis
        devices = set()
        for entry in entries:
            if entry.parsed_telegram:
                if hasattr(entry.parsed_telegram, "serial_number"):
                    devices.add(entry.parsed_telegram.serial_number)
                elif hasattr(entry.parsed_telegram, "module_type"):
                    devices.add(f"Module_{entry.parsed_telegram.module_type}")

        return {
            "total_entries": total_entries,
            "valid_parses": valid_parses,
            "parse_errors": parse_errors,
            "parse_success_rate": (
                (valid_parses / total_entries * 100) if total_entries > 0 else 0
            ),
            "direction_counts": {"tx": tx_count, "rx": rx_count},
            "telegram_type_counts": {
                "event": event_count,
                "system": system_count,
                "reply": reply_count,
                "unknown": unknown_count,
            },
            "checksum_validation": {
                "validated_count": len(validated_entries),
                "valid_checksums": valid_checksums,
                "invalid_checksums": invalid_checksums,
                "validation_success_rate": (
                    (valid_checksums / len(validated_entries) * 100)
                    if validated_entries
                    else 0
                ),
            },
            "time_range": {
                "start": (
                    start_time.strftime("%H:%M:%S.%f")[:-3] if start_time else None
                ),
                "end": end_time.strftime("%H:%M:%S.%f")[:-3] if end_time else None,
                "duration_ms": duration_ms,
                "duration_seconds": duration_ms / 1000 if duration_ms > 0 else 0,
            },
            "devices": sorted(list(devices)),
        }

    @staticmethod
    def filter_entries(
        entries: List[LogEntry],
        telegram_type: Optional[str] = None,
        direction: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[LogEntry]:
        """Filter log entries based on criteria.

        Args:
            entries: List of LogEntry objects to filter.
            telegram_type: Filter by telegram type (event, system, reply).
            direction: Filter by direction (TX, RX).
            start_time: Filter entries after this time.
            end_time: Filter entries before this time.

        Returns:
            Filtered list of LogEntry objects.
        """
        filtered = entries.copy()

        if telegram_type:
            filtered = [e for e in filtered if e.telegram_type == telegram_type.lower()]

        if direction:
            filtered = [e for e in filtered if e.direction == direction.upper()]

        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]

        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]

        return filtered
