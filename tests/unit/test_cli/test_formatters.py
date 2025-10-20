"""Tests for CLI output formatters."""

import json
from typing import Any
from unittest.mock import Mock

from xp.cli.utils.formatters import (
    ListFormatter,
    OutputFormatter,
    StatisticsFormatter,
    TelegramFormatter,
)


class TestOutputFormatter:
    """Test OutputFormatter class."""

    def test_init_default(self):
        """Test default initialization."""
        formatter = OutputFormatter()
        assert formatter.json_output is False

    def test_init_json_mode(self):
        """Test JSON mode initialization."""
        formatter = OutputFormatter(json_output=True)
        assert formatter.json_output is True

    def test_success_response_text_mode(self):
        """Test success response in text mode."""
        formatter = OutputFormatter(json_output=False)
        data = {
            "telegram": "<E14L00I02M>",
            "serial_number": "12345",
            "operation": "test",
            "count": 5,
        }
        result = formatter.success_response(data)
        assert "Telegram: <E14L00I02M>" in result
        assert "Serial: 12345" in result
        assert "Operation: test" in result
        assert "Count: 5" in result

    def test_success_response_json_mode(self):
        """Test success response in JSON mode."""
        formatter = OutputFormatter(json_output=True)
        data = {"telegram": "<E14L00I02M>", "serial_number": "12345"}
        result = formatter.success_response(data)
        parsed = json.loads(result)
        assert parsed["telegram"] == "<E14L00I02M>"
        assert parsed["serial_number"] == "12345"

    def test_error_response_text_mode(self):
        """Test error response in text mode."""
        result = OutputFormatter(json_output=False).error_response("Connection failed")
        assert result == "Error: Connection failed"

    def test_error_response_json_mode(self):
        """Test error response in JSON mode."""
        result = OutputFormatter(json_output=True).error_response("Connection failed")
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["error"] == "Connection failed"

    def test_error_response_with_extra_data(self):
        """Test error response with additional data."""
        result = OutputFormatter(json_output=True).error_response(
            "Connection failed", extra_data={"retry_count": 3}
        )
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["error"] == "Connection failed"
        assert parsed["retry_count"] == 3

    def test_validation_response_valid_text_mode(self):
        """Test validation response for valid input in text mode."""
        result = OutputFormatter(json_output=False).validation_response(
            True, {"checksum": "ABC"}
        )
        assert "✓ Valid" in result

    def test_validation_response_invalid_text_mode(self):
        """Test validation response for invalid input in text mode."""
        result = OutputFormatter(json_output=False).validation_response(
            False, {"checksum": "ABC"}
        )
        assert "✗ Invalid" in result

    def test_validation_response_json_mode(self):
        """Test validation response in JSON mode."""
        result = OutputFormatter(json_output=True).validation_response(
            True, {"checksum": "ABC"}
        )
        parsed = json.loads(result)
        assert parsed["valid"] is True
        assert parsed["checksum"] == "ABC"

    def test_checksum_status_valid_text_mode(self):
        """Test checksum status valid in text mode."""
        result = OutputFormatter(json_output=False).checksum_status(True)
        assert result == "✓ Valid"

    def test_checksum_status_invalid_text_mode(self):
        """Test checksum status invalid in text mode."""
        result = OutputFormatter(json_output=False).checksum_status(False)
        assert result == "✗ Invalid"

    def test_checksum_status_json_mode(self):
        """Test checksum status in JSON mode."""
        result = OutputFormatter(json_output=True).checksum_status(True)
        parsed = json.loads(result)
        assert parsed["checksum_valid"] is True

    def test_format_text_response_with_additional_fields(self):
        """Test formatting text response with various field types."""
        formatter = OutputFormatter(json_output=False)
        data = {
            "telegram": "<TEST>",
            "additional_field": "value",
            "number_field": 42,
            "float_field": 3.15,
        }
        result = formatter.success_response(data)
        assert "Telegram: <TEST>" in result
        assert "Additional Field: value" in result
        assert "Number Field: 42" in result
        assert "Float Field: 3.15" in result


class TestTelegramFormatter:
    """Test TelegramFormatter class."""

    def test_format_telegram_summary_json_mode(self):
        """Test telegram summary in JSON mode."""
        formatter = TelegramFormatter(json_output=True)
        telegram_data = {
            "telegram_type": "event",
            "raw_telegram": "<E14L00I02M>",
            "timestamp": "2025-01-01T00:00:00",
        }
        result = formatter.format_telegram_summary(telegram_data)
        parsed = json.loads(result)
        assert parsed["telegram_type"] == "event"
        assert parsed["raw_telegram"] == "<E14L00I02M>"

    def test_format_telegram_summary_with_service_formatter(self):
        """Test telegram summary with service formatter method."""
        formatter = TelegramFormatter(json_output=False)
        telegram_data = {"telegram_type": "event"}
        service_formatter_method = "Formatted by service"
        result = formatter.format_telegram_summary(
            telegram_data, service_formatter_method
        )
        assert result == "Formatted by service"

    def test_format_telegram_summary_fallback(self):
        """Test telegram summary fallback formatting."""
        formatter = TelegramFormatter(json_output=False)
        telegram_data = {
            "telegram_type": "event",
            "raw_telegram": "<E14L00I02M>",
            "timestamp": "2025-01-01T00:00:00",
        }
        result = formatter.format_telegram_summary(telegram_data)
        assert "Type: Event" in result
        assert "Raw: <E14L00I02M>" in result
        assert "Timestamp: 2025-01-01T00:00:00" in result

    def test_format_validation_result_json_mode(self):
        """Test validation result in JSON mode."""
        formatter = TelegramFormatter(json_output=True)
        mock_telegram = Mock()
        mock_telegram.to_dict.return_value = {
            "telegram_type": "event",
            "raw": "<TEST>",
        }
        result = formatter.format_validation_result(mock_telegram, True, "Summary")
        parsed = json.loads(result)
        assert parsed["telegram_type"] == "event"
        assert parsed["checksum_valid"] is True

    def test_format_validation_result_text_mode_valid(self):
        """Test validation result in text mode with valid checksum."""
        formatter = TelegramFormatter(json_output=False)
        mock_telegram = Mock()
        result = formatter.format_validation_result(
            mock_telegram, True, "Event telegram"
        )
        assert "Event telegram" in result
        assert "✓ Valid" in result

    def test_format_validation_result_text_mode_invalid(self):
        """Test validation result in text mode with invalid checksum."""
        formatter = TelegramFormatter(json_output=False)
        mock_telegram = Mock()
        result = formatter.format_validation_result(
            mock_telegram, False, "Event telegram"
        )
        assert "Event telegram" in result
        assert "✗ Invalid" in result

    def test_format_validation_result_text_mode_no_checksum(self):
        """Test validation result with no checksum validation."""
        formatter = TelegramFormatter(json_output=False)
        mock_telegram = Mock()
        result = formatter.format_validation_result(
            mock_telegram, None, "Event telegram"
        )
        assert "Event telegram" in result
        assert "Checksum validation" not in result

    def test_format_telegram_summary_empty_data(self):
        """Test formatting telegram summary with empty data."""
        result = TelegramFormatter(json_output=False).format_telegram_summary({})
        assert result == ""

    def test_format_telegram_summary_partial_data(self):
        """Test formatting telegram summary with partial data."""
        result = TelegramFormatter(json_output=False).format_telegram_summary(
            {"telegram_type": "event"}
        )
        assert "Type: Event" in result


class TestListFormatter:
    """Test ListFormatter class."""

    def test_format_list_response_json_mode(self):
        """Test list response in JSON mode."""
        items = ["item1", "item2", "item3"]
        result = ListFormatter(json_output=True).format_list_response(
            items, "Test Items"
        )
        parsed = json.loads(result)
        assert parsed["count"] == 3
        assert parsed["items"] == ["item1", "item2", "item3"]

    def test_format_list_response_json_mode_with_to_dict(self):
        """Test list response in JSON mode with objects having to_dict."""
        formatter = ListFormatter(json_output=True)
        mock_item = Mock()
        mock_item.to_dict.return_value = {"name": "test", "value": 123}
        items = [mock_item]
        result = formatter.format_list_response(items, "Test Items")
        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["name"] == "test"

    def test_format_list_response_text_mode(self):
        """Test list response in text mode."""
        formatter = ListFormatter(json_output=False)
        items = ["item1", "item2", "item3"]
        result = formatter.format_list_response(items, "Test Items")
        assert "Test Items: 3 items" in result
        assert "1. item1" in result
        assert "2. item2" in result
        assert "3. item3" in result

    def test_format_list_response_with_custom_formatter(self):
        """Test list response with custom item formatter."""
        formatter = ListFormatter(json_output=False)
        items = [{"name": "item1"}, {"name": "item2"}]

        def item_formatter(x: Any) -> str:
            """Format item for display.

            Args:
                x: Item dictionary to format.

            Returns:
                Formatted string representation of the item.
            """
            return f"Name: {x['name']}"

        result = formatter.format_list_response(
            items, "Test Items", item_formatter=item_formatter
        )
        assert "1. Name: item1" in result
        assert "2. Name: item2" in result

    def test_format_search_results_json_mode(self):
        """Test search results in JSON mode."""
        formatter = ListFormatter(json_output=True)
        matches = ["result1", "result2"]
        result = formatter.format_search_results(matches, "test query")
        parsed = json.loads(result)
        assert parsed["query"] == "test query"
        assert parsed["count"] == 2
        assert parsed["matches"] == ["result1", "result2"]

    def test_format_search_results_text_mode_with_results(self):
        """Test search results in text mode with matches."""
        formatter = ListFormatter(json_output=False)
        mock_item = Mock()
        mock_item.code = 1
        mock_item.name = "Test"
        mock_item.description = "Test description"
        matches = [mock_item]
        result = formatter.format_search_results(matches, "test")
        assert "Found 1 items matching 'test'" in result
        assert "Test" in result
        assert "Test description" in result

    def test_format_search_results_text_mode_no_results(self):
        """Test search results in text mode with no matches."""
        result = ListFormatter(json_output=False).format_search_results(
            [], "test query"
        )
        assert result == "No items found matching 'test query'"

    def test_format_search_results_text_mode_without_attributes(self):
        """Test search results with items lacking code/name/description."""
        matches = ["simple_string"]
        result = ListFormatter(json_output=False).format_search_results(matches, "test")
        assert "Found 1 items matching 'test'" in result
        assert "simple_string" in result


class TestStatisticsFormatter:
    """Test StatisticsFormatter class."""

    def test_format_file_statistics_json_mode(self):
        """Test file statistics in JSON mode."""
        formatter = StatisticsFormatter(json_output=True)
        stats = {
            "time_range": {
                "start": "2025-01-01 00:00:00",
                "end": "2025-01-01 01:00:00",
                "duration_seconds": 3600,
            },
            "telegram_type_counts": {"event": 10, "system": 5},
            "direction_counts": {"rx": 8, "tx": 7},
            "total_entries": 15,
        }
        result = formatter.format_file_statistics("/tmp/test.log", stats, 15)
        parsed = json.loads(result)
        assert parsed["file_path"] == "/tmp/test.log"
        assert parsed["entry_count"] == 15
        assert parsed["statistics"]["time_range"]["start"] == "2025-01-01 00:00:00"

    def test_format_file_statistics_text_mode_complete(self):
        """Test file statistics in text mode with complete data."""
        formatter = StatisticsFormatter(json_output=False)
        stats = {
            "time_range": {
                "start": "2025-01-01 00:00:00",
                "end": "2025-01-01 01:00:00",
                "duration_seconds": 3600.5,
            },
            "telegram_type_counts": {"event": 10, "system": 5},
            "direction_counts": {"rx": 8, "tx": 7},
            "total_entries": 15,
        }
        result = formatter.format_file_statistics("/tmp/test.log", stats, 15)
        assert "Console Bus Log Summary" in result
        assert "File: /tmp/test.log" in result
        assert "Entries: 15" in result
        assert "Time Range: 2025-01-01 00:00:00 - 2025-01-01 01:00:00" in result
        assert "Duration: 3600.500 seconds" in result
        assert "Telegram Distribution:" in result
        assert "Event: 10 (66.7%)" in result
        assert "System: 5 (33.3%)" in result
        assert "Direction Distribution:" in result
        assert "RX: 8 (53.3%)" in result
        assert "TX: 7 (46.7%)" in result

    def test_format_file_statistics_text_mode_no_time_range(self):
        """Test file statistics without time range data."""
        formatter = StatisticsFormatter(json_output=False)
        stats = {
            "time_range": {},
            "telegram_type_counts": {"event": 5},
            "direction_counts": {"rx": 5},
            "total_entries": 5,
        }
        result = formatter.format_file_statistics("/tmp/test.log", stats, 5)
        assert "Console Bus Log Summary" in result
        assert "File: /tmp/test.log" in result
        assert "Time Range:" not in result

    def test_format_file_statistics_text_mode_empty_stats(self):
        """Test file statistics with empty statistics."""
        formatter = StatisticsFormatter(json_output=False)
        stats = {
            "time_range": {},
            "telegram_type_counts": {},
            "direction_counts": {},
            "total_entries": 0,
        }
        result = formatter.format_file_statistics("/tmp/test.log", stats, 0)
        assert "Console Bus Log Summary" in result
        assert "Entries: 0" in result
