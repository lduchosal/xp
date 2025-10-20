"""Service for device discover telegram operations.

This service handles generation and parsing of device discover system telegrams
used for enumerating all connected devices on the console bus.
"""

from typing import List, Set

from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.utils.checksum import calculate_checksum


class DiscoverError(Exception):
    """Raised when discover operations fail."""

    pass


class DeviceInfo:
    """Information about a discovered device."""

    def __init__(
        self, serial_number: str, checksum_valid: bool = True, raw_telegram: str = ""
    ):
        """Initialize device info.

        Args:
            serial_number: 10-digit module serial number.
            checksum_valid: Whether the telegram checksum is valid.
            raw_telegram: Raw telegram string.
        """
        self.serial_number = serial_number
        self.checksum_valid = checksum_valid
        self.raw_telegram = raw_telegram

    def __str__(self) -> str:
        """Return string representation of device.

        Returns:
            String with serial number and checksum status.
        """
        status = "✓" if self.checksum_valid else "✗"
        return f"Device {self.serial_number} ({status})"

    def __repr__(self) -> str:
        """Return repr representation of device.

        Returns:
            DeviceInfo constructor representation.
        """
        return f"DeviceInfo(serial='{self.serial_number}', checksum_valid={self.checksum_valid})"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with device information.
        """
        return {
            "serial_number": self.serial_number,
            "checksum_valid": self.checksum_valid,
            "raw_telegram": self.raw_telegram,
        }


class TelegramDiscoverService:
    """
    Service for generating and handling device discover telegrams.

    Handles discover broadcasting and response parsing:
    - Discover request: <S0000000000F01D00{checksum}>
    - Discover responses: <R{serial}F01D{checksum}>
    """

    def __init__(self) -> None:
        """Initialize the discover service."""
        pass

    @staticmethod
    def generate_discover_telegram() -> str:
        """
        Generate a broadcast discover telegram to enumerate all devices.

        Returns:
            Formatted discover telegram string: "<S0000000000F01D00FA>"
        """
        # Build the data part of the telegram
        # S0000000000F01D00 - Broadcast (all zeros) discover command
        data_part = "S0000000000F01D00"

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Build complete telegram
        telegram = f"<{data_part}{checksum}>"

        return telegram

    def create_discover_telegram_object(self) -> SystemTelegram:
        """Create a SystemTelegram object for discover broadcast.

        Returns:
            SystemTelegram object representing the discover command.
        """
        raw_telegram = self.generate_discover_telegram()

        # Extract checksum from the generated telegram
        checksum = raw_telegram[-3:-1]  # Get checksum before closing >

        telegram = SystemTelegram(
            serial_number="0000000000",  # Broadcast address
            system_function=SystemFunction.DISCOVERY,
            datapoint_type=None,
            checksum=checksum,
            raw_telegram=raw_telegram,
        )

        return telegram

    @staticmethod
    def is_discover_response(reply_telegram: ReplyTelegram) -> bool:
        """Check if a reply telegram is a discover response.

        Args:
            reply_telegram: Reply telegram to check.

        Returns:
            True if this is a discover response, False otherwise.
        """
        return reply_telegram.system_function == SystemFunction.DISCOVERY

    @staticmethod
    def _generate_discover_response(serial_number: str) -> str:
        """Generate discover response telegram for a device.

        Args:
            serial_number: 10-digit module serial number.

        Returns:
            Formatted discover response telegram.
        """
        # Format: <R{serial}F01D{checksum}>
        data_part = f"R{serial_number}F01D"
        checksum = calculate_checksum(data_part)
        telegram = f"<{data_part}{checksum}>"
        return telegram

    @staticmethod
    def get_unique_devices(devices: List[DeviceInfo]) -> List[DeviceInfo]:
        """Filter out duplicate devices based on serial number.

        Args:
            devices: List of discovered devices.

        Returns:
            List of unique devices (first occurrence of each serial number).
        """
        seen_serials: Set[str] = set()
        unique_devices = []

        for device in devices:
            if device.serial_number not in seen_serials:
                seen_serials.add(device.serial_number)
                unique_devices.append(device)

        return unique_devices

    @staticmethod
    def validate_discover_response_format(raw_telegram: str) -> bool:
        """Validate if a raw telegram matches discover response format.

        Args:
            raw_telegram: Raw telegram string to validate.

        Returns:
            True if format matches discover response pattern.
        """
        # Discover response format: <R{10-digit-serial}F01D{2-char-checksum}>
        import re

        match = re.compile(r"^<R(\d{10})F01D([A-Z0-9]{2})>$").match(
            raw_telegram.strip()
        )

        return match is not None

    def generate_discover_summary(self, devices: List[DeviceInfo]) -> dict:
        """Generate a summary of a discover results.

        Args:
            devices: List of discovered devices.

        Returns:
            Dictionary with discover statistics.
        """
        unique_devices = self.get_unique_devices(devices)
        valid_devices = [d for d in unique_devices if d.checksum_valid]
        invalid_devices = [d for d in unique_devices if not d.checksum_valid]

        # Group by serial number prefixes for pattern analysis
        serial_prefixes = {}
        for device in unique_devices:
            prefix = device.serial_number[:4]  # First 4 digits
            if prefix not in serial_prefixes:
                serial_prefixes[prefix] = 0
            serial_prefixes[prefix] += 1

        return {
            "total_responses": len(devices),
            "unique_devices": len(unique_devices),
            "valid_checksums": len(valid_devices),
            "invalid_checksums": len(invalid_devices),
            "success_rate": (
                (len(valid_devices) / len(unique_devices) * 100)
                if unique_devices
                else 0
            ),
            "duplicate_responses": len(devices) - len(unique_devices),
            "serial_prefixes": serial_prefixes,
            "device_list": [device.serial_number for device in valid_devices],
        }

    def format_discover_results(self, devices: List[DeviceInfo]) -> str:
        """Format discover results for human-readable output.

        Args:
            devices: List of discovered devices.

        Returns:
            Formatted string summary.
        """
        if not devices:
            return "No devices discovered"

        summary = self.generate_discover_summary(devices)
        unique_devices = self.get_unique_devices(devices)

        lines = [
            "=== Device Discover Results ===",
            f"Total Responses: {summary['total_responses']}",
            f"Unique Devices: {summary['unique_devices']}",
            f"Valid Checksums: {summary['valid_checksums']}/{summary['unique_devices']} ({summary['success_rate']:.1f}%)",
        ]

        if summary["duplicate_responses"] > 0:
            lines.append(f"Duplicate Responses: {summary['duplicate_responses']}")

        lines.extend("\nDiscovered Devices:")
        lines.append("-" * 40)

        for device in unique_devices:
            status_icon = "✓" if device.checksum_valid else "✗"
            lines.append(f"{status_icon} {device.serial_number}")

        if summary["serial_prefixes"]:
            lines.append("\nSerial Number Distribution:")
            for prefix, count in sorted(summary["serial_prefixes"].items()):
                lines.append(f"  {prefix}xxxx: {count} device(s)")

        return "\n".join(lines)

    @staticmethod
    def is_discover_request(telegram: SystemTelegram) -> bool:
        """Check if telegram is a discover request.

        Args:
            telegram: System telegram to check.

        Returns:
            True if this is a discover request, False otherwise.
        """
        return (
            telegram.system_function == SystemFunction.DISCOVERY
            and telegram.serial_number == "0000000000"
        )  # Broadcast address
