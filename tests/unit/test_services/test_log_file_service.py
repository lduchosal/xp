"""Tests for LogFileService."""

from datetime import datetime
from typing import cast
from unittest.mock import Mock, patch

import pytest

from xp.models.log_entry import LogEntry
from xp.models.telegram.event_telegram import EventTelegram
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.log_file_service import LogFileParsingError, LogFileService
from xp.services.telegram.telegram_service import TelegramParsingError, TelegramService


class TestLogFileService:
    """Test cases for LogFileService."""

    def test_init_with_default_telegram_service(self):
        """Test initialization with default telegram service."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)
        assert isinstance(service.telegram_service, TelegramService)

    def test_init_with_custom_telegram_service(self):
        """Test initialization with custom telegram service."""
        mock_telegram_service = Mock()
        service = LogFileService(mock_telegram_service)
        assert service.telegram_service == mock_telegram_service

    def test_parse_log_line_valid(self):
        """Test parsing a valid log line."""
        mock_telegram_service = Mock(spec=TelegramService)
        service = LogFileService(mock_telegram_service)
        line = "22:44:20,352 [TX] <S0012345008F27D00AAFN>"

        # Mock telegram service
        mock_telegram = Mock(spec=SystemTelegram)
        service.telegram_service.parse_telegram = Mock(return_value=mock_telegram)

        result = service._parse_log_line(line, 1)

        assert result is not None
        assert result.line_number == 1
        assert result.direction == "TX"
        assert result.raw_telegram == "<S0012345008F27D00AAFN>"
        assert result.parsed_telegram == mock_telegram
        assert result.parse_error is None

        # Verify telegram service was called
        service.telegram_service.parse_telegram.assert_called_once_with(
            "<S0012345008F27D00AAFN>"
        )

    def test_parse_log_line_telegram_parsing_error(self):
        """Test parsing log line with telegram parsing error."""
        mock_telegram_service = Mock(spec=TelegramService)
        service = LogFileService(mock_telegram_service)
        line = "22:44:20,352 [RX] <invalid>"

        # Mock telegram service to raise error
        service.telegram_service.parse_telegram = Mock(
            side_effect=TelegramParsingError("Invalid telegram format")
        )

        result = service._parse_log_line(line, 5)

        assert result is not None
        assert result.line_number == 5
        assert result.direction == "RX"
        assert result.raw_telegram == "<invalid>"
        assert result.parsed_telegram is None
        assert result.parse_error == "Invalid telegram format"

    def test_parse_log_line_invalid_format(self):
        """Test parsing invalid log line format."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)
        invalid_lines = [
            "invalid line format",
            "22:44:20,352 <missing direction>",
            "[TX] <missing timestamp>",
            "22:44:20,352 [TX] missing telegram",
            "",  # empty line would be filtered out before reaching this method
        ]

        for invalid_line in invalid_lines:
            with pytest.raises(LogFileParsingError, match="Invalid log line format"):
                service._parse_log_line(invalid_line, 1)

    def test_parse_log_lines_valid(self):
        """Test parsing multiple valid log lines."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)
        lines = [
            "22:44:20,352 [TX] <S0012345008F27D00AAFN>",
            "22:44:20,420 [RX] <R0012345008F18DFA>",
            "22:44:20,467 [RX] <E07L06I80BAL>",
            "",  # Empty line should be skipped
            "  ",  # Whitespace-only line should be skipped
        ]

        # Mock telegram service
        mock_telegrams = [
            Mock(spec=SystemTelegram),
            Mock(spec=SystemTelegram),
            Mock(spec=EventTelegram),
        ]
        service.telegram_service.parse_telegram = Mock(side_effect=mock_telegrams)

        results = service.parse_log_lines(lines)

        assert len(results) == 3  # Empty lines should be skipped

        # Check first entry
        assert results[0].line_number == 1
        assert results[0].direction == "TX"
        assert results[0].raw_telegram == "<S0012345008F27D00AAFN>"
        assert results[0].parsed_telegram == mock_telegrams[0]

        # Check second entry
        assert results[1].line_number == 2
        assert results[1].direction == "RX"
        assert results[1].raw_telegram == "<R0012345008F18DFA>"

        # Check third entry
        assert results[2].line_number == 3
        assert results[2].direction == "RX"
        assert results[2].raw_telegram == "<E07L06I80BAL>"

    def test_parse_log_lines_with_errors(self):
        """Test parsing log lines with various errors."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        lines = [
            "22:44:20,352 [TX] <valid>",
            "invalid line format",
            "22:44:20,420 [RX] <another_valid>",
        ]

        # Mock telegram service - first and third calls succeed, second fails
        mock_telegram = Mock(spec=SystemTelegram)
        service.telegram_service.parse_telegram = Mock(
            side_effect=[mock_telegram, mock_telegram]  # Only two valid telegrams
        )

        results = service.parse_log_lines(lines)

        assert len(results) == 3

        # First entry should be valid
        assert results[0].parsed_telegram == mock_telegram
        assert results[0].parse_error is None

        # Second entry should have parse error
        assert results[1].parsed_telegram is None
        assert results[1].parse_error is not None
        assert "Line parsing failed" in results[1].parse_error

        # Third entry should be valid
        assert results[2].parsed_telegram == mock_telegram
        assert results[2].parse_error is None

    @patch("pathlib.Path.exists")
    def test_parse_log_file_not_found(self, mock_exists):
        """Test parsing non-existent log file."""
        mock_exists.return_value = False

        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        with pytest.raises(LogFileParsingError, match="Log file not found"):
            service.parse_log_file("/nonexistent/log.txt")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_parse_log_file_not_file(self, mock_is_file, mock_exists):
        """Test parsing when path is not a file."""
        mock_exists.return_value = True
        mock_is_file.return_value = False

        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        with pytest.raises(LogFileParsingError, match="Path is not a file"):
            service.parse_log_file("/path/to/directory")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("builtins.open")
    def test_parse_log_file_io_error(self, mock_file_open, mock_is_file, mock_exists):
        """Test parsing with IO error."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_file_open.side_effect = IOError("Permission denied")

        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        with pytest.raises(LogFileParsingError, match="Error reading log file"):
            service.parse_log_file("/path/to/log.txt")

    def test_validate_log_format_valid(self):
        """Test log format validation with valid file."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        # Mock parse_log_file to return valid entries
        valid_entry = Mock(spec=LogEntry)
        valid_entry.is_valid_parse = True
        service.parse_log_file = Mock(return_value=[valid_entry])

        result = service.validate_log_format("/path/to/log.txt")
        assert result is True

    def test_validate_log_format_no_valid_entries(self):
        """Test log format validation with no valid entries."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        # Mock parse_log_file to return only invalid entries
        invalid_entry = Mock(spec=LogEntry)
        invalid_entry.is_valid_parse = False
        service.parse_log_file = Mock(return_value=[invalid_entry])

        result = service.validate_log_format("/path/to/log.txt")
        assert result is False

    def test_validate_log_format_parsing_error(self):
        """Test log format validation with parsing error."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)
        service.parse_log_file = Mock(side_effect=LogFileParsingError("Error"))

        result = service.validate_log_format("/path/to/log.txt")
        assert result is False

    @patch.object(LogFileService, "parse_log_file")
    def test_extract_telegrams(self, mock_parse):
        """Test extracting telegrams from log file."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        # Mock parse_log_file
        entries = [
            Mock(raw_telegram="<telegram1>"),
            Mock(raw_telegram="<telegram2>"),
            Mock(raw_telegram="<telegram3>"),
        ]
        mock_parse.return_value = entries

        result = service.extract_telegrams("/path/to/log.txt")
        expected = ["<telegram1>", "<telegram2>", "<telegram3>"]

        assert result == expected

    def test_get_file_statistics_empty(self):
        """Test statistics for empty entry list."""
        telegram_service = Mock(spec=TelegramService)

        stats = LogFileService(telegram_service).get_file_statistics([])

        assert stats == {"total_entries": 0}

    def test_get_file_statistics_full(self):
        """Test comprehensive statistics calculation."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        # Create mock entries with various properties
        entries = []

        # Valid event telegram
        event_entry = Mock(spec=LogEntry)
        event_entry.is_valid_parse = True
        event_entry.direction = "RX"
        event_entry.telegram_type = "E"
        event_entry.checksum_validated = True
        event_entry.timestamp = datetime(2023, 1, 1, 22, 44, 20, 352000)

        # Create a simple object with only module_type
        class EventTelegramMock:
            """Mock event telegram for testing.

            Attributes:
                module_type: The module type identifier.
            """

            module_type = 14

        event_entry.parsed_telegram = EventTelegramMock()
        entries.append(event_entry)

        # Valid system telegram
        system_entry = Mock(spec=LogEntry)
        system_entry.is_valid_parse = True
        system_entry.direction = "TX"
        system_entry.telegram_type = "S"
        system_entry.checksum_validated = True
        system_entry.timestamp = datetime(2023, 1, 1, 22, 44, 25, 500000)

        # Create a simple object with only serial_number
        class SystemTelegramMock:
            """Mock system telegram for testing.

            Attributes:
                serial_number: The device serial number.
            """

            serial_number = "0012345008"

        system_entry.parsed_telegram = SystemTelegramMock()
        entries.append(system_entry)

        # Invalid entry
        invalid_entry = Mock(spec=LogEntry)
        invalid_entry.is_valid_parse = False
        invalid_entry.direction = "TX"
        invalid_entry.telegram_type = "unknown"
        invalid_entry.checksum_validated = None
        invalid_entry.timestamp = datetime(2023, 1, 1, 22, 44, 22, 0)
        invalid_entry.parsed_telegram = None
        entries.append(invalid_entry)

        stats = service.get_file_statistics(cast(list[LogEntry], entries))

        # Check basic counts
        assert stats["total_entries"] == 3
        assert stats["valid_parses"] == 2
        assert stats["parse_errors"] == 1
        assert stats["parse_success_rate"] == pytest.approx(66.67, rel=1e-2)

        # Check direction counts
        assert stats["direction_counts"]["tx"] == 2
        assert stats["direction_counts"]["rx"] == 1

        # Check telegram type counts
        assert stats["telegram_type_counts"]["event"] == 1
        assert stats["telegram_type_counts"]["system"] == 1
        assert stats["telegram_type_counts"]["reply"] == 0
        assert stats["telegram_type_counts"]["unknown"] == 1

        # Check checksum validation
        assert stats["checksum_validation"]["validated_count"] == 2
        assert stats["checksum_validation"]["valid_checksums"] == 2
        assert stats["checksum_validation"]["invalid_checksums"] == 0
        assert stats["checksum_validation"]["validation_success_rate"] == 100.0

        # Check time range
        assert stats["time_range"]["start"] == "22:44:20.352"
        assert stats["time_range"]["end"] == "22:44:25.500"
        assert stats["time_range"]["duration_ms"] == 5148
        assert stats["time_range"]["duration_seconds"] == 5.148

        # Check devices
        assert "0012345008" in stats["devices"]
        assert "Module_14" in stats["devices"]

    def test_filter_entries_by_type(self):
        """Test filtering entries by telegram type."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        entries = [
            Mock(telegram_type="event"),
            Mock(telegram_type="system"),
            Mock(telegram_type="reply"),
            Mock(telegram_type="event"),
        ]

        result = service.filter_entries(
            cast(list[LogEntry], entries), telegram_type="event"
        )
        assert len(result) == 2
        assert all(entry.telegram_type == "event" for entry in result)

    def test_filter_entries_by_direction(self):
        """Test filtering entries by direction."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        entries = [
            Mock(direction="TX"),
            Mock(direction="RX"),
            Mock(direction="TX"),
            Mock(direction="RX"),
        ]

        result = service.filter_entries(cast(list[LogEntry], entries), direction="TX")
        assert len(result) == 2
        assert all(entry.direction == "TX" for entry in result)

    def test_filter_entries_by_time_range(self):
        """Test filtering entries by time range."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        base_time = datetime(2023, 1, 1, 22, 44, 20)
        entries = [
            Mock(timestamp=base_time),  # 22:44:20
            Mock(timestamp=base_time.replace(second=25)),  # 22:44:25
            Mock(timestamp=base_time.replace(second=30)),  # 22:44:30
            Mock(timestamp=base_time.replace(second=35)),  # 22:44:35
        ]

        # Filter to entries between 22:44:22 and 22:44:32
        start_time = base_time.replace(second=22)
        end_time = base_time.replace(second=32)

        result = service.filter_entries(
            cast(list[LogEntry], entries), start_time=start_time, end_time=end_time
        )
        assert len(result) == 2  # Should include 22:44:25 and 22:44:30

        timestamps = [entry.timestamp for entry in result]
        assert base_time.replace(second=25) in timestamps
        assert base_time.replace(second=30) in timestamps

    def test_filter_entries_multiple_criteria(self):
        """Test filtering entries with multiple criteria."""
        telegram_service = Mock(spec=TelegramService)
        service = LogFileService(telegram_service)

        base_time = datetime(2023, 1, 1, 22, 44, 20)
        entries = [
            Mock(telegram_type="event", direction="TX", timestamp=base_time),
            Mock(
                telegram_type="event",
                direction="RX",
                timestamp=base_time.replace(second=25),
            ),
            Mock(
                telegram_type="system",
                direction="TX",
                timestamp=base_time.replace(second=30),
            ),
            Mock(
                telegram_type="event",
                direction="TX",
                timestamp=base_time.replace(second=35),
            ),
        ]

        # Filter for event telegrams, TX direction, after 22:44:22
        start_time = base_time.replace(second=22)
        result = service.filter_entries(
            cast(list[LogEntry], entries),
            telegram_type="event",
            direction="TX",
            start_time=start_time,
        )

        assert len(result) == 1  # Only the last entry matches all criteria
        assert result[0].telegram_type == "event"
        assert result[0].direction == "TX"
        assert result[0].timestamp == base_time.replace(second=35)
