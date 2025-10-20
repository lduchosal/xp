"""XP output service for handling XP output device operations."""

import re
from typing import Dict

from xp.models.telegram.action_type import ActionType
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.output_telegram import OutputTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.services.telegram.telegram_service import TelegramService
from xp.utils.checksum import calculate_checksum


class XPOutputError(Exception):
    """Raised when XP24 action operations fail."""

    pass


class TelegramOutputService:
    """Service for XP action operations.

    Handles parsing and validation of XP24 action telegrams,
    status queries, and action command generation.

    Attributes:
        MAX_OUTPUTS: Maximum number of outputs supported.
        XP_OUTPUT_PATTERN: Regex pattern for XP24 action telegrams.
        XP_ACK_NAK_PATTERN: Regex pattern for ACK/NAK response telegrams.
        telegram_service: TelegramService instance for parsing.
    """

    MAX_OUTPUTS = 99

    # Regex pattern for XP24 action telegrams
    XP_OUTPUT_PATTERN = re.compile(r"^<S(\d{10})F27D(\d{2})(A[AB])([A-Z0-9]{2})>$")
    XP_ACK_NAK_PATTERN = re.compile(r"^<R(\d{10})F(1[89])D([A-Z0-9]{2})>$")

    def __init__(self, telegram_service: TelegramService) -> None:
        """Initialize the XP output service.

        Args:
            telegram_service: TelegramService instance for parsing operations.
        """
        self.telegram_service = telegram_service

    def validate_output_number(self, output_number: int) -> None:
        """Validate XP24 output number according to architecture constraints.

        Args:
            output_number: Output number to validate (0-3).

        Raises:
            XPOutputError: If output number is invalid.
        """
        if not isinstance(output_number, int):
            raise XPOutputError(
                f"Output number must be integer, got {type(output_number)}"
            )

        if not (0 <= output_number <= self.MAX_OUTPUTS):
            raise XPOutputError(
                f"Invalid output number: {output_number}. "
                f"XP24 supports outputs 0-{self.MAX_OUTPUTS}"
            )

    @staticmethod
    def validate_serial_number(serial_number: str) -> None:
        """Validate serial number format.

        Args:
            serial_number: Serial number to validate.

        Raises:
            XPOutputError: If serial number is invalid.
        """
        if not isinstance(serial_number, str):
            raise XPOutputError(
                f"Serial number must be string, got {type(serial_number)}"
            )

        if len(serial_number) != 10 or not serial_number.isdigit():
            raise XPOutputError(
                f"Invalid serial number: {serial_number}. "
                "Serial number must be exactly 10 digits"
            )

    def generate_system_action_telegram(
        self, serial_number: str, output_number: int, action: ActionType
    ) -> str:
        """Generate XP24 action telegram string.

        Args:
            serial_number: Target module serial number.
            output_number: Output number (0-3).
            action: Action type (PRESS/RELEASE).

        Returns:
            Complete telegram string with checksum.

        Raises:
            XPOutputError: If parameters are invalid.
        """
        # Validate outputs according to architecture constraints
        self.validate_serial_number(serial_number)
        self.validate_output_number(output_number)

        if not isinstance(action, ActionType):
            raise XPOutputError(f"Invalid action type: {action}")

        function_code = SystemFunction.ACTION.value
        # Build data part without checksum
        data_part = (
            f"S{serial_number}F{function_code}D{output_number:02d}{action.value}"
        )

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Return complete telegram
        return f"<{data_part}{checksum}>"

    def generate_system_status_telegram(self, serial_number: str) -> str:
        """Generate XP output status query telegram.

        Args:
            serial_number: Target module serial number.

        Returns:
            Complete status query telegram string.
        """
        # Validate outputs
        self.validate_serial_number(serial_number)
        function_code = SystemFunction.READ_DATAPOINT.value
        datapoint_code = DataPointType.MODULE_OUTPUT_STATE.value

        # Build data part without checksum
        data_part = f"S{serial_number}F{function_code}D{datapoint_code}"

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Return complete telegram
        return f"<{data_part}{checksum}>"

    def parse_reply_telegram(self, raw_telegram: str) -> OutputTelegram:
        """Parse a raw XP output response telegram string.

        Args:
            raw_telegram: The raw telegram string (e.g., "<R0012345003F18DFF>").

        Returns:
            XPOutputTelegram object with parsed data.

        Raises:
            XPOutputError: If telegram format is invalid.
        """
        if not raw_telegram:
            raise XPOutputError("Empty telegram string")

        # Validate and parse using regex
        match = self.XP_ACK_NAK_PATTERN.match(raw_telegram.strip())
        if not match:
            raise XPOutputError(
                f"Invalid XP24 response telegram format: {raw_telegram}"
            )

        try:
            serial_number = match.group(1)
            ack_nak = match.group(2)
            checksum = match.group(3)

            # Parse action type
            system_function = SystemFunction.from_code(ack_nak)
            if system_function is None:
                raise XPOutputError(f"Unknown system_function: {ack_nak}")

            # Create telegram object
            telegram = OutputTelegram(
                serial_number=serial_number,
                system_function=system_function,
                checksum=checksum,
                raw_telegram=raw_telegram,
            )

            # Validate checksum
            telegram.checksum_validated = self.telegram_service.validate_checksum(
                telegram
            )

            return telegram

        except ValueError as e:
            raise XPOutputError(f"Invalid values in XP24 action telegram: {e}")

    def parse_system_telegram(self, raw_telegram: str) -> OutputTelegram:
        """Parse a raw XP output telegram string.

        Args:
            raw_telegram: The raw telegram string (e.g., "<S0012345008F27D00AAFN>").

        Returns:
            XPOutputTelegram object with parsed data.

        Raises:
            XPOutputError: If telegram format is invalid.
        """
        if not raw_telegram:
            raise XPOutputError("Empty telegram string")

        # Validate and parse using regex
        match = self.XP_OUTPUT_PATTERN.match(raw_telegram.strip())
        if not match:
            raise XPOutputError(f"Invalid XP24 action telegram format: {raw_telegram}")

        try:
            serial_number = match.group(1)
            output_number = int(match.group(2))
            action_code = match.group(3)
            checksum = match.group(4)

            # Validate output number
            self.validate_output_number(output_number)

            # Parse action type
            action_type = ActionType.from_code(action_code)
            if action_type is None:
                raise XPOutputError(f"Unknown action code: {action_code}")

            # Create telegram object
            telegram = OutputTelegram(
                serial_number=serial_number,
                output_number=output_number,
                action_type=action_type,
                checksum=checksum,
                raw_telegram=raw_telegram,
            )

            # Validate checksum
            telegram.checksum_validated = self.telegram_service.validate_checksum(
                telegram
            )

            return telegram

        except ValueError as e:
            raise XPOutputError(f"Invalid values in XP24 action telegram: {e}")

    def parse_status_response(self, raw_telegram: str) -> list[bool]:
        """Parse XP24 status response telegram to extract output states.

        Args:
            raw_telegram: Raw reply telegram (e.g., "<R0012345008F02D12xxxx1110FJ>").

        Returns:
            Dictionary mapping output numbers (0-3) to their states (True=ON, False=OFF).

        Raises:
            XPOutputError: If output telegram is invalid.
        """
        if not raw_telegram:
            raise XPOutputError("Empty status response telegram")

        # Look for status pattern in reply telegram
        reply_telegram = self.telegram_service.parse_reply_telegram(raw_telegram)
        if not reply_telegram or not reply_telegram.data_value:
            raise XPOutputError("Not a reply telegram")

        if (
            not reply_telegram.datapoint_type
            or not reply_telegram.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        ):
            raise XPOutputError("Not a DataPoint telegram")

        status_bits = reply_telegram.data_value.replace("xxxx", "")[::-1][0:4]
        if len(status_bits) != 4:
            raise XPOutputError("Not a module_output_state telegram")

        status = [False, False, False, False]
        for i in range(4):
            status[i] = status_bits[i] == "1"

        return status

    @staticmethod
    def format_status_summary(status: Dict[int, bool]) -> str:
        """Format status dictionary into human-readable summary.

        Args:
            status: Dictionary mapping output numbers to states.

        Returns:
            Formatted status summary string.
        """
        lines = ["XP24 Output Status:"]
        for output_num in sorted(status.keys()):
            state = "ON" if status[output_num] else "OFF"
            lines.append(f"  Output {output_num}: {state}")

        return "\n".join(lines)

    @staticmethod
    def format_action_summary(telegram: OutputTelegram) -> str:
        """Format XP24 action telegram for human-readable output.

        Args:
            telegram: The parsed action telegram.

        Returns:
            Formatted string summary.
        """
        checksum_status = ""
        if telegram.checksum_validated is not None:
            status_indicator = "✓" if telegram.checksum_validated else "✗"
            checksum_status = f" ({status_indicator})"

        return (
            f"XP Output: {telegram}\n"
            f"Raw: {telegram.raw_telegram}\n"
            f"Timestamp: {telegram.timestamp}\n"
            f"Checksum: {telegram.checksum}{checksum_status}"
        )
