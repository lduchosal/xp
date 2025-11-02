"""Telegram Service for parsing XP telegrams.

This module provides telegram parsing functionality for event, system, and reply telegrams.
"""

import logging
import re
from typing import Union

from xp.models import EventType
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.event_telegram import EventTelegram
from xp.models.telegram.output_telegram import OutputTelegram
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.models.telegram.telegram_type import TelegramType
from xp.utils.checksum import calculate_checksum


class TelegramParsingError(Exception):
    """Raised when telegram parsing fails."""

    pass


class TelegramService:
    """Service for parsing event telegrams from the console bus.

    Handles parsing of telegrams in the format:
    <[EO]{module_type}L{link_number}I{output_number}{event_type}{checksum}>

    Attributes:
        EVENT_TELEGRAM_PATTERN: Regex pattern for event telegrams.
        SYSTEM_TELEGRAM_PATTERN: Regex pattern for system telegrams.
        REPLY_TELEGRAM_PATTERN: Regex pattern for reply telegrams.
    """

    # <O06L00I07MAG>
    # <O06L00I07BAJ>
    # <E13L12I02BAB>
    EVENT_TELEGRAM_PATTERN = re.compile(
        r"^<([EO])(\d{1,2})L(\d{2})I(\d{2})([MB])([A-Z0-9]{2})>$"
    )

    SYSTEM_TELEGRAM_PATTERN = re.compile(r"^<S(\d{10})F(\d{2})D(.{2,})([A-Z0-9]{2})>$")

    REPLY_TELEGRAM_PATTERN = re.compile(r"^<R(\d{10})F(\d{2})(.+?)([A-Z0-9]{2})>$")

    def __init__(self) -> None:
        """Initialize the telegram service."""
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def parse_event_telegram(self, raw_telegram: str) -> EventTelegram:
        """Parse a raw telegram string into an EventTelegram object.

        Args:
            raw_telegram: The raw telegram string (e.g., "<E14L00I02MAK>").

        Returns:
            EventTelegram object with parsed data.

        Raises:
            TelegramParsingError: If the telegram format is invalid.
        """
        if not raw_telegram:
            raise TelegramParsingError("Empty telegram string")

        # Validate and parse using regex
        match = self.EVENT_TELEGRAM_PATTERN.match(raw_telegram.strip())
        if not match:
            raise TelegramParsingError(f"Invalid telegram format: {raw_telegram}")

        try:
            event_telegram_type = match.group(1)
            module_type = int(match.group(2))
            link_number = int(match.group(3))
            output_number = int(match.group(4))
            event_type_char = match.group(5)
            checksum = match.group(6)

            # Validate ranges
            if event_telegram_type not in ("E", "O"):
                raise TelegramParsingError(
                    f"Event telegram type (E or O): {event_telegram_type}"
                )

            if not (0 <= link_number <= 99):
                raise TelegramParsingError(
                    f"Link number out of range (0-99): {link_number}"
                )

            if not (0 <= output_number <= 99):
                raise TelegramParsingError(
                    f"Input number out of range (0-99): {output_number}"
                )

            # Parse event type
            try:
                event_type = EventType(event_type_char)
            except ValueError:
                raise TelegramParsingError(f"Invalid event type: {event_type_char}")

            # Create the telegram object
            telegram = EventTelegram(
                module_type=module_type,
                link_number=link_number,
                input_number=output_number,
                event_type=event_type,
                checksum=checksum,
                raw_telegram=raw_telegram,
            )

            # Automatically validate checksum
            telegram.checksum_validated = self.validate_checksum(telegram)

            return telegram

        except ValueError as e:
            raise TelegramParsingError(f"Invalid numeric values in telegram: {e}")

    @staticmethod
    def validate_checksum(
        telegram: Union[EventTelegram, ReplyTelegram, SystemTelegram, OutputTelegram],
    ) -> bool:
        """Validate the checksum of a parsed telegram.

        Args:
            telegram: The parsed telegram.

        Returns:
            True if checksum is valid, False otherwise.
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

    @staticmethod
    def format_event_telegram_summary(telegram: EventTelegram) -> str:
        """Format a telegram for human-readable output.

        Args:
            telegram: The parsed telegram.

        Returns:
            Formatted string summary.
        """
        checksum_status = ""
        if telegram.checksum_validated is not None:
            status_indicator = "✓" if telegram.checksum_validated else "✗"
            checksum_status = f" ({status_indicator})"

        return (
            f"Event: {telegram}\n"
            f"Raw: {telegram.raw_telegram}\n"
            f"Timestamp: {telegram.timestamp}\n"
            f"Checksum: {telegram.checksum}{checksum_status}"
        )

    def parse_system_telegram(self, raw_telegram: str) -> SystemTelegram:
        """Parse a raw system telegram string into a SystemTelegram object.

        Args:
            raw_telegram: The raw telegram string (e.g., "<S0020012521F02D18FN>").

        Returns:
            SystemTelegram object with parsed data.

        Raises:
            TelegramParsingError: If the telegram format is invalid.
        """
        if not raw_telegram:
            raise TelegramParsingError("Empty telegram string")

        # Validate and parse using regex
        match = self.SYSTEM_TELEGRAM_PATTERN.match(raw_telegram.strip())
        if not match:
            raise TelegramParsingError(
                f"Invalid system telegram format: {raw_telegram}"
            )

        try:
            serial_number = match.group(1)
            function_code = match.group(2)
            data = match.group(3)
            checksum = match.group(4)

            # Parse system function
            system_function = SystemFunction.from_code(function_code)
            if system_function is None:
                raise TelegramParsingError(
                    f"Unknown system function code: {function_code}"
                )

            # Parse data point type
            datapoint_type = None
            if system_function == SystemFunction.READ_DATAPOINT:
                datapoint_type = DataPointType.from_code(data)

            # Create the telegram object
            telegram = SystemTelegram(
                serial_number=serial_number,
                system_function=system_function,
                data=data,
                datapoint_type=datapoint_type,
                checksum=checksum,
                raw_telegram=raw_telegram,
            )

            # Automatically validate checksum
            telegram.checksum_validated = self.validate_checksum(telegram)

            return telegram

        except ValueError as e:
            raise TelegramParsingError(f"Invalid values in system telegram: {e}")

    def parse_reply_telegram(self, raw_telegram: str) -> ReplyTelegram:
        """Parse a raw reply telegram string into a ReplyTelegram object.

        Args:
            raw_telegram: The raw telegram string (e.g., "<R0020012521F02D18+26,0§CIL>").

        Returns:
            ReplyTelegram object with parsed data.

        Raises:
            TelegramParsingError: If the telegram format is invalid.
        """
        if not raw_telegram:
            raise TelegramParsingError("Empty telegram string")

        # Validate and parse using regex
        self.logger.debug(f"Parsing reply telegram {raw_telegram}")
        match = self.REPLY_TELEGRAM_PATTERN.match(raw_telegram.strip())
        if not match:
            raise TelegramParsingError(f"Invalid reply telegram format: {raw_telegram}")

        try:
            serial_number = match.group(1)
            function_code = match.group(2)
            full_data_value = match.group(3)
            checksum = match.group(4)

            # Parse system function
            system_function = SystemFunction.from_code(function_code)
            if system_function is None:
                raise TelegramParsingError(
                    f"Unknown system function code: {function_code}"
                )

            # Parse data point and data value from full_data_value
            if full_data_value.startswith("D") and len(full_data_value) >= 3:
                # Regular reply format: D{data_point}{data}
                data = full_data_value[1:3]
                data_value = full_data_value[3:] if len(full_data_value) > 3 else ""
            else:
                # ACK/NAK format: just data (like "D" for ACK/NAK)
                data = "00"  # Default to STATUS
                data_value = full_data_value

            # Parse data point type
            data_point_type = DataPointType.from_code(data)

            # Create the telegram object
            telegram = ReplyTelegram(
                serial_number=serial_number,
                system_function=system_function,
                data=data,
                datapoint_type=data_point_type,
                data_value=data_value,
                checksum=checksum,
                raw_telegram=raw_telegram,
            )

            # Automatically validate checksum
            telegram.checksum_validated = self.validate_checksum(telegram)

            return telegram

        except ValueError as e:
            raise TelegramParsingError(f"Invalid values in reply telegram: {e}")

    def parse_telegram(
        self, raw_telegram: str
    ) -> Union[EventTelegram, SystemTelegram, ReplyTelegram]:
        """Auto-detect and parse any type of telegram.

        Args:
            raw_telegram: The raw telegram string.

        Returns:
            Appropriate telegram object based on type.

        Raises:
            TelegramParsingError: If the telegram format is invalid or unknown.
        """
        if not raw_telegram:
            raise TelegramParsingError("Empty telegram string")

        # Then check general telegram types
        telegram_type_code = (
            raw_telegram.strip()[1] if len(raw_telegram.strip()) > 1 else ""
        )

        if telegram_type_code in (TelegramType.EVENT.value, TelegramType.CPEVENT.value):
            return self.parse_event_telegram(raw_telegram)
        elif telegram_type_code == TelegramType.SYSTEM.value:
            return self.parse_system_telegram(raw_telegram)
        elif telegram_type_code == TelegramType.REPLY.value:
            return self.parse_reply_telegram(raw_telegram)
        else:
            raise TelegramParsingError(
                f"Unknown telegram type code: {telegram_type_code}"
            )

    @staticmethod
    def format_system_telegram_summary(telegram: SystemTelegram) -> str:
        """Format a system telegram for human-readable output.

        Args:
            telegram: The parsed system telegram.

        Returns:
            Formatted string summary.
        """
        checksum_status = ""
        if telegram.checksum_validated is not None:
            status_indicator = "✓" if telegram.checksum_validated else "✗"
            checksum_status = f" ({status_indicator})"

        return (
            f"System: {telegram}\n"
            f"Raw: {telegram.raw_telegram}\n"
            f"Timestamp: {telegram.timestamp}\n"
            f"Checksum: {telegram.checksum}{checksum_status}"
        )

    @staticmethod
    def format_reply_telegram_summary(telegram: ReplyTelegram) -> str:
        """Format a reply telegram for human-readable output.

        Args:
            telegram: The parsed reply telegram.

        Returns:
            Formatted string summary.
        """
        parsed_data = telegram.parse_datapoint_value
        data_display = (
            parsed_data.get("formatted", telegram.data_value)
            if parsed_data.get("parsed")
            else telegram.data_value
        )

        checksum_status = ""
        if telegram.checksum_validated is not None:
            status_indicator = "✓" if telegram.checksum_validated else "✗"
            checksum_status = f" ({status_indicator})"

        return (
            f"Reply: {telegram}\n"
            f"Data: {data_display}\n"
            f"Raw: {telegram.raw_telegram}\n"
            f"Timestamp: {telegram.timestamp}\n"
            f"Checksum: {telegram.checksum}{checksum_status}"
        )
