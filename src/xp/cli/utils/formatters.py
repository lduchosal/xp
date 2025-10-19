"""Output formatting utilities for CLI commands."""

import json
from typing import Any, Dict, Optional


class OutputFormatter:
    """Handles standardized output formatting for CLI commands."""

    def __init__(self, json_output: bool = False):
        """Initialize the output formatter.

        Args:
            json_output: Whether to format output as JSON (default: False).
        """
        self.json_output = json_output

    def success_response(self, data: Dict[str, Any]) -> str:
        """Format a successful response.

        Args:
            data: Response data to format.

        Returns:
            Formatted success response as string.
        """
        if self.json_output:
            return json.dumps(data, indent=2)
        return self._format_text_response(data)

    def error_response(
        self, error: str, extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format an error response.

        Args:
            error: Error message.
            extra_data: Additional error data to include.

        Returns:
            Formatted error response as string.
        """
        error_data = {"success": False, "error": error}
        if extra_data:
            error_data.update(extra_data)

        if self.json_output:
            return json.dumps(error_data, indent=2)
        return f"Error: {error}"

    def validation_response(self, is_valid: bool, data: Dict[str, Any]) -> str:
        """Format a validation response.

        Args:
            is_valid: Whether validation passed.
            data: Validation data to include.

        Returns:
            Formatted validation response as string.
        """
        if self.json_output:
            response_data = {"valid": is_valid} | data
            return json.dumps(response_data, indent=2)

        status = "✓ Valid" if is_valid else "✗ Invalid"
        return f"Status: {status}"

    def checksum_status(self, is_valid: bool) -> str:
        """Format checksum validation status.

        Args:
            is_valid: Whether checksum is valid.

        Returns:
            Formatted checksum status as string.
        """
        if self.json_output:
            return json.dumps({"checksum_valid": is_valid}, indent=2)

        return "✓ Valid" if is_valid else "✗ Invalid"

    @staticmethod
    def _format_text_response(data: Dict[str, Any]) -> str:
        """Format data for human-readable text output.

        Args:
            data: Data dictionary to format.

        Returns:
            Formatted text output as string.
        """
        lines = []

        # Handle common data patterns
        if "telegram" in data:
            lines.append(f"Telegram: {data['telegram']}")

        if "serial_number" in data:
            lines.append(f"Serial: {data['serial_number']}")

        if "operation" in data:
            lines.append(f"Operation: {data['operation']}")

        if "count" in data:
            lines.append(f"Count: {data['count']}")

        # Add any remaining fields
        for key, value in data.items():
            if key not in ("telegram", "serial_number", "operation", "count"):
                if isinstance(value, (str, int, float)):
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return "\n".join(lines)


class TelegramFormatter(OutputFormatter):
    """Specialized formatter for telegram-related output."""

    def format_telegram_summary(
        self, telegram_data: Dict[str, Any], service_formatter_method: Any = None
    ) -> str:
        """Format telegram summary using service method when available.

        Args:
            telegram_data: Telegram data to format.
            service_formatter_method: Optional service formatter method.

        Returns:
            Formatted telegram summary as string.
        """
        if self.json_output:
            return json.dumps(telegram_data, indent=2)

        if service_formatter_method:
            return str(service_formatter_method)

        # Fallback formatting
        lines = []
        if "telegram_type" in telegram_data:
            lines.append(f"Type: {telegram_data['telegram_type'].title()}")
        if "raw_telegram" in telegram_data:
            lines.append(f"Raw: {telegram_data['raw_telegram']}")
        if "timestamp" in telegram_data:
            lines.append(f"Timestamp: {telegram_data['timestamp']}")

        return "\n".join(lines)

    def format_validation_result(
        self, parsed_telegram: Any, checksum_valid: Optional[bool], service_summary: str
    ) -> str:
        """Format telegram validation results.

        Args:
            parsed_telegram: Parsed telegram object.
            checksum_valid: Whether checksum is valid.
            service_summary: Summary from service.

        Returns:
            Formatted validation result as string.
        """
        if self.json_output:
            output = parsed_telegram.to_dict()
            output["checksum_valid"] = checksum_valid
            return json.dumps(output, indent=2)

        lines = [service_summary]
        if checksum_valid is not None:
            status = "✓ Valid" if checksum_valid else "✗ Invalid"
            lines.append(f"Checksum validation: {status}")

        return "\n".join(lines)


class ListFormatter(OutputFormatter):
    """Specialized formatter for list-based output."""

    def format_list_response(
        self, items: list, title: str, item_formatter: Any = None
    ) -> str:
        """Format a list of items with optional custom formatter.

        Args:
            items: List of items to format.
            title: Title for the list.
            item_formatter: Optional custom formatter function.

        Returns:
            Formatted list as string.
        """
        if self.json_output:
            return json.dumps(
                {
                    "items": [
                        item.to_dict() if hasattr(item, "to_dict") else item
                        for item in items
                    ],
                    "count": len(items),
                },
                indent=2,
            )

        lines = [f"{title}: {len(items)} items", "-" * 50]

        for i, item in enumerate(items, 1):
            if item_formatter:
                lines.append(f"{i}. {item_formatter(item)}")
            elif hasattr(item, "__str__"):
                lines.append(f"{i}. {item}")
            else:
                lines.append(f"{i}. {item}")

        return "\n".join(lines)

    def format_search_results(self, matches: list, query: str) -> str:
        """Format search results.

        Args:
            matches: List of matching items.
            query: Search query string.

        Returns:
            Formatted search results as string.
        """
        if self.json_output:
            return json.dumps(
                {
                    "query": query,
                    "matches": [
                        item.to_dict() if hasattr(item, "to_dict") else item
                        for item in matches
                    ],
                    "count": len(matches),
                },
                indent=2,
            )

        if not matches:
            return f"No items found matching '{query}'"

        lines = [f"Found {len(matches)} items matching '{query}':", "-" * 60]
        for item in matches:
            if (
                hasattr(item, "code")
                and hasattr(item, "name")
                and hasattr(item, "description")
            ):
                lines.append(f"{item.code:2} - {item.name}: {item.description}")
            else:
                lines.append(str(item))

        return "\n".join(lines)


class StatisticsFormatter(OutputFormatter):
    """Specialized formatter for statistics and analysis output."""

    def format_file_statistics(
        self, file_path: str, stats: Dict[str, Any], entry_count: int
    ) -> str:
        """Format file analysis statistics.

        Args:
            file_path: Path to the analyzed file.
            stats: Statistics dictionary.
            entry_count: Total number of entries.

        Returns:
            Formatted statistics as string.
        """
        if self.json_output:
            return json.dumps(
                {
                    "file_path": file_path,
                    "statistics": stats,
                    "entry_count": entry_count,
                },
                indent=2,
            )

        lines = [
            "=== Console Bus Log Summary ===",
            f"File: {file_path}",
            f"Entries: {entry_count}",
        ]

        # Time range
        if stats.get("time_range", {}).get("start"):
            time_range = stats["time_range"]
            lines.extend(
                [
                    f"Time Range: {time_range['start']} - {time_range['end']}",
                    f"Duration: {time_range['duration_seconds']:.3f} seconds",
                ]
            )

        # Telegram distribution
        lines.append("\nTelegram Distribution:")
        type_counts = stats.get("telegram_type_counts", {})
        total = stats.get("total_entries", 0)

        for t_type, count in type_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"  {t_type.capitalize()}: {count} ({percentage:.1f}%)")

        # Direction distribution
        lines.append("\nDirection Distribution:")
        dir_counts = stats.get("direction_counts", {})
        for direction, count in dir_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"  {direction.upper()}: {count} ({percentage:.1f}%)")

        return "\n".join(lines)
