"""Service for link number telegram operations.

This service handles generation and parsing of link number system telegrams
used for setting and reading module link numbers.
"""

from contextlib import suppress
from typing import Optional

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.utils.checksum import calculate_checksum


class LinkNumberError(Exception):
    """Raised when link number operations fail."""

    pass


class LinkNumberService:
    """
    Service for generating and handling link number system telegrams.

    Handles telegrams for setting module link numbers using the F04D04 format:
    <S{serial_number}F04D04{link_number}{checksum}>
    """

    def __init__(self) -> None:
        """Initialize the link number service."""
        pass

    @staticmethod
    def generate_set_link_number_telegram(serial_number: str, link_number: int) -> str:
        """Generate a telegram to set a module's link number.

        Args:
            serial_number: The 10-digit module serial number.
            link_number: The link number to set (0-99).

        Returns:
            Formatted telegram string (e.g., "<S0012345005F04D0425FO>").

        Raises:
            LinkNumberError: If parameters are invalid.
        """
        # Validate serial number
        if not serial_number or len(serial_number) != 10:
            raise LinkNumberError(
                f"Serial number must be 10 digits, got: {serial_number}"
            )

        if not serial_number.isdigit():
            raise LinkNumberError(
                f"Serial number must contain only digits: {serial_number}"
            )

        # Validate link number range
        if not (0 <= link_number <= 99):
            raise LinkNumberError(
                f"Link number must be between 0-99, got: {link_number}"
            )

        # Format link number with leading zero if needed
        link_number_str = f"{link_number:02d}"

        # Build the data part of the telegram
        data_part = f"S{serial_number}F04D04{link_number_str}"

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Build complete telegram
        telegram = f"<{data_part}{checksum}>"

        return telegram

    @staticmethod
    def generate_read_link_number_telegram(serial_number: str) -> str:
        """Generate a telegram to read a module's current link number.

        Args:
            serial_number: The 10-digit module serial number.

        Returns:
            Formatted telegram string for reading link number.

        Raises:
            LinkNumberError: If serial number is invalid.
        """
        # Validate serial number
        if not serial_number or len(serial_number) != 10:
            raise LinkNumberError(
                f"Serial number must be 10 digits, got: {serial_number}"
            )

        if not serial_number.isdigit():
            raise LinkNumberError(
                f"Serial number must contain only digits: {serial_number}"
            )

        # Build the data part for reading (F03D04 - READ_CONFIG, LINK_NUMBER)
        data_part = f"S{serial_number}F03D04"

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Build complete telegram
        telegram = f"<{data_part}{checksum}>"

        return telegram

    def create_set_link_number_telegram_object(
        self, serial_number: str, link_number: int
    ) -> SystemTelegram:
        """Create a SystemTelegram object for setting link number.

        Args:
            serial_number: The 10-digit module serial number.
            link_number: The link number to set (0-99).

        Returns:
            SystemTelegram object representing the set link number command.
        """
        raw_telegram = self.generate_set_link_number_telegram(
            serial_number, link_number
        )

        # Extract checksum from the generated telegram
        checksum = raw_telegram[-3:-1]  # Get checksum before closing >

        telegram = SystemTelegram(
            serial_number=serial_number,
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum=checksum,
            raw_telegram=raw_telegram,
        )

        return telegram

    def create_read_link_number_telegram_object(
        self, serial_number: str
    ) -> SystemTelegram:
        """Create a SystemTelegram object for reading link number.

        Args:
            serial_number: The 10-digit module serial number.

        Returns:
            SystemTelegram object representing the read link number command.
        """
        raw_telegram = self.generate_read_link_number_telegram(serial_number)

        # Extract checksum from the generated telegram
        checksum = raw_telegram[-3:-1]  # Get checksum before closing >

        telegram = SystemTelegram(
            serial_number=serial_number,
            system_function=SystemFunction.READ_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum=checksum,
            raw_telegram=raw_telegram,
        )

        return telegram

    @staticmethod
    def parse_link_number_from_reply(reply_telegram: ReplyTelegram) -> Optional[int]:
        """Parse the link number value from a reply telegram.

        Args:
            reply_telegram: Reply telegram containing link number data.

        Returns:
            Link number if successfully parsed, None otherwise.
        """
        if (
            reply_telegram.datapoint_type != DataPointType.LINK_NUMBER
            or not reply_telegram.data_value
        ):
            return None

        with suppress(ValueError, TypeError):
            # The data value should contain the link number
            link_number = int(reply_telegram.data_value)
            if 0 <= link_number <= 99:
                return link_number

        return None

    @staticmethod
    def is_ack_response(reply_telegram: ReplyTelegram) -> bool:
        """Check if a reply telegram is an ACK response.

        Args:
            reply_telegram: Reply telegram to check.

        Returns:
            True if this is an ACK response (F18D), False otherwise.
        """
        return reply_telegram.system_function == SystemFunction.ACK

    @staticmethod
    def is_nak_response(reply_telegram: ReplyTelegram) -> bool:
        """Check if a reply telegram is a NAK response.

        Args:
            reply_telegram: Reply telegram to check.

        Returns:
            True if this is a NAK response (F19D), False otherwise.
        """
        return reply_telegram.system_function == SystemFunction.NAK
