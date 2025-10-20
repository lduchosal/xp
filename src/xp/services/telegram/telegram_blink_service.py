"""Service for blink/unblink telegram operations.

This service handles generation and parsing of blink/unblink system telegrams
used for controlling module LED status.
"""

from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.utils.checksum import calculate_checksum


class BlinkError(Exception):
    """Raised when blink/unblink operations fail."""

    pass


class TelegramBlinkService:
    """
    Service for generating and handling blink/unblink system telegrams.

    Handles telegrams for controlling module LED status using the F05D00 and F06D00 formats:
    - Blink: <S{serial_number}F05D00{checksum}>
    - Unblink: <S{serial_number}F06D00{checksum}>
    """

    def __init__(self) -> None:
        """Initialize the blink service."""
        pass

    @staticmethod
    def generate_blink_telegram(serial_number: str, on_or_off: str) -> str:
        """Generate a telegram to start blinking a module's LED.

        Args:
            serial_number: The 10-digit module serial number.
            on_or_off: The action to perform ('on' for blink, 'off' for unblink).

        Returns:
            Formatted telegram string (e.g., "<S0012345008F05D00FN>").

        Raises:
            BlinkError: If parameters are invalid.
        """
        # Validate serial number
        if not serial_number or len(serial_number) != 10:
            raise BlinkError(f"Serial number must be 10 digits, got: {serial_number}")

        if not serial_number.isdigit():
            raise BlinkError(f"Serial number must contain only digits: {serial_number}")

        action_type = SystemFunction.BLINK
        if on_or_off.lower() == "off":
            action_type = SystemFunction.UNBLINK

        # Build the data part of the telegram (F05D00 - Blink function, Status data point)
        data_part = f"S{serial_number}F{action_type.value}D00"

        # Calculate checksum
        checksum = calculate_checksum(data_part)

        # Build complete telegram
        telegram = f"<{data_part}{checksum}>"

        return telegram

    def create_blink_telegram_object(self, serial_number: str) -> SystemTelegram:
        """Create a SystemTelegram object for blinking LED.

        Args:
            serial_number: The 10-digit module serial number.

        Returns:
            SystemTelegram object representing the blink command.
        """
        raw_telegram = self.generate_blink_telegram(serial_number, "on")

        # Extract checksum from the generated telegram
        checksum = raw_telegram[-3:-1]  # Get checksum before closing >

        telegram = SystemTelegram(
            serial_number=serial_number,
            system_function=SystemFunction.BLINK,
            datapoint_type=None,
            checksum=checksum,
            raw_telegram=raw_telegram,
        )

        return telegram

    def create_unblink_telegram_object(self, serial_number: str) -> SystemTelegram:
        """Create a SystemTelegram object for unblink LED.

        Args:
            serial_number: The 10-digit module serial number.

        Returns:
            SystemTelegram object representing the unblink command.
        """
        raw_telegram = self.generate_blink_telegram(serial_number, "off")

        # Extract checksum from the generated telegram
        checksum = raw_telegram[-3:-1]  # Get checksum before closing >

        telegram = SystemTelegram(
            serial_number=serial_number,
            system_function=SystemFunction.UNBLINK,
            datapoint_type=None,
            checksum=checksum,
            raw_telegram=raw_telegram,
        )

        return telegram

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
