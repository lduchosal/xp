"""XP input service for handling XP input device operations."""

import re
from typing import Dict, Optional
from ..models.input_telegram import InputTelegram
from ..models.action_type import ActionType
from ..utils.checksum import calculate_checksum


class XPInputError(Exception):
    """Raised when XP24 action operations fail"""

    pass


class XPInputService:
    """
    Service for XP action operations.

    Handles parsing and validation of XP24 action telegrams,
    status queries, and action command generation.
    """

    # XP24 specific constants
    MAX_INPUTS = 4  # XP24 has exactly 4 inputs (0-3)
    MODULE_TYPE = 7  # XP24 module type code
    ACTION_FUNCTION = "27"  # Function code for XP24 actions
    STATUS_FUNCTION = "02"  # Function code for status queries
    STATUS_DATAPOINT = "12"  # Data point code for input status

    # Regex pattern for XP24 action telegrams
    XP_INPUT_PATTERN = re.compile(r"^<S(\d{10})F27D(\d{2})([A-Z0-9]{2})([A-Z0-9]{2})>$")

    def __init__(self):
        """Initialize the XP input service"""
        pass

    def validate_input_number(self, input_number: int) -> None:
        """
        Validate XP24 input number according to architecture constraints.

        Args:
            input_number: Input number to validate (0-3)

        Raises:
            XPInputError: If input number is invalid
        """
        if not isinstance(input_number, int):
            raise XPInputError(
                f"Input number must be integer, got {type(input_number)}"
            )

        if not (0 <= input_number < self.MAX_INPUTS):
            raise XPInputError(
                f"Invalid input number: {input_number}. "
                f"XP24 supports inputs 0-{self.MAX_INPUTS-1}"
            )

    def validate_serial_number(self, serial_number: str) -> None:
        """
        Validate serial number format.

        Args:
            serial_number: Serial number to validate

        Raises:
            XP24ActionError: If serial number is invalid
        """
        if not isinstance(serial_number, str):
            raise XPInputError(
                f"Serial number must be string, got {type(serial_number)}"
            )

        if len(serial_number) != 10 or not serial_number.isdigit():
            raise XPInputError(
                f"Invalid serial number: {serial_number}. "
                "Serial number must be exactly 10 digits"
            )

    def generate_input_telegram(
        self, serial_number: str, input_number: int, action: ActionType
    ) -> str:
        """
        Generate XP24 action telegram string.

        Args:
            serial_number: Target module serial number
            input_number: Input number (0-3)
            action: Action type (PRESS/RELEASE)

        Returns:
            Complete telegram string with checksum

        Raises:
            XP24ActionError: If parameters are invalid
        """
        # Validate inputs according to architecture constraints
        self.validate_serial_number(serial_number)
        self.validate_input_number(input_number)

        if not isinstance(action, ActionType):
            raise XPInputError(f"Invalid action type: {action}")

        # Build data part without checksum
        data_part = (
            f"S{serial_number}F{self.ACTION_FUNCTION}D{input_number:02d}{action.value}"
        )

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Return complete telegram
        return f"<{data_part}{checksum}>"

    def generate_input_status_telegram(self, serial_number: str) -> str:
        """
        Generate XP input status query telegram.

        Args:
            serial_number: Target module serial number

        Returns:
            Complete status query telegram string

        Raises:
            XPInputError: If serial number is invalid
        """
        # Validate inputs
        self.validate_serial_number(serial_number)

        # Build data part without checksum
        data_part = f"S{serial_number}F{self.STATUS_FUNCTION}D{self.STATUS_DATAPOINT}"

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Return complete telegram
        return f"<{data_part}{checksum}>"

    def parse_input_telegram(self, raw_telegram: str) -> InputTelegram:
        """
        Parse a raw XP input telegram string.

        Args:
            raw_telegram: The raw telegram string (e.g., "<S0020044964F27D00AAFN>")

        Returns:
            XPInputTelegram object with parsed data

        Raises:
            XPInputError: If telegram format is invalid
        """
        if not raw_telegram:
            raise XPInputError("Empty telegram string")

        # Validate and parse using regex
        match = self.XP_INPUT_PATTERN.match(raw_telegram.strip())
        if not match:
            raise XPInputError(f"Invalid XP24 action telegram format: {raw_telegram}")

        try:
            serial_number = match.group(1)
            input_number = int(match.group(2))
            action_code = match.group(3)
            checksum = match.group(4)

            # Validate input number
            self.validate_input_number(input_number)

            # Parse action type
            action_type = ActionType.from_code(action_code)
            if action_type is None:
                raise XPInputError(f"Unknown action code: {action_code}")

            # Create telegram object
            telegram = InputTelegram(
                serial_number=serial_number,
                input_number=input_number,
                action_type=action_type,
                checksum=checksum,
                raw_telegram=raw_telegram,
            )

            # Validate checksum
            telegram.checksum_validated = self.validate_checksum(telegram)

            return telegram

        except ValueError as e:
            raise XPInputError(f"Invalid values in XP24 action telegram: {e}")

    def validate_checksum(self, telegram: InputTelegram) -> bool:
        """
        Validate the checksum of a parsed XP24 action telegram.

        Args:
            telegram: The parsed telegram

        Returns:
            True if checksum is valid, False otherwise
        """
        if not telegram.checksum or len(telegram.checksum) != 2:
            return False

        # Extract the data part (everything between < and checksum)
        raw = telegram.raw_telegram
        if not raw.startswith("<") or not raw.endswith(">"):
            return False

        # Get the data part without brackets and checksum
        data_part = raw[1:-3]  # Remove '<' and last 2 chars (checksum) + '>'

        # Calculate expected checksum
        expected_checksum = calculate_checksum(data_part)

        return telegram.checksum == expected_checksum

    def parse_status_response(self, raw_telegram: str) -> Dict[int, bool]:
        """
        Parse XP24 status response telegram to extract input states.

        Args:
            raw_telegram: Raw reply telegram (e.g., "<R0020044964F02D12xxxx1110FJ>")

        Returns:
            Dictionary mapping input numbers (0-3) to their states (True=ON, False=OFF)

        Raises:
            XP24ActionError: If telegram format is invalid
        """
        if not raw_telegram:
            raise XPInputError("Empty status response telegram")

        # Look for status pattern in reply telegram
        status_match = re.search(r"F02D12xxxx(\d{4})", raw_telegram)
        if not status_match:
            raise XPInputError(f"Invalid status response format: {raw_telegram}")

        status_bits = status_match.group(1)
        if len(status_bits) != 4:
            raise XPInputError(f"Invalid status bits length: {status_bits}")

        # Map each bit to input state
        status = {}
        for i in range(4):
            status[i] = status_bits[i] == "1"

        return status

    def format_status_summary(self, status: Dict[int, bool]) -> str:
        """
        Format status dictionary into human-readable summary.

        Args:
            status: Dictionary mapping input numbers to states

        Returns:
            Formatted status summary string
        """
        lines = ["XP24 Input Status:"]
        for input_num in sorted(status.keys()):
            state = "ON" if status[input_num] else "OFF"
            lines.append(f"  Input {input_num}: {state}")

        return "\n".join(lines)

    def format_action_summary(self, telegram: InputTelegram) -> str:
        """
        Format XP24 action telegram for human-readable output.

        Args:
            telegram: The parsed action telegram

        Returns:
            Formatted string summary
        """
        checksum_status = ""
        if telegram.checksum_validated is not None:
            status_indicator = "✓" if telegram.checksum_validated else "✗"
            checksum_status = f" ({status_indicator})"

        return (
            f"XP Input: {telegram}\n"
            f"Raw: {telegram.raw_telegram}\n"
            f"Timestamp: {telegram.timestamp}\n"
            f"Checksum: {telegram.checksum}{checksum_status}"
        )
