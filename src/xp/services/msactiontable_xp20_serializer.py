"""Serializer for XP20 Action Table telegram encoding/decoding."""

from ..models.msactiontable_xp20 import InputChannel, Xp20MsActionTable
from ..utils.checksum import de_nibble, nibble


class Xp20MsActionTableSerializer:
    """Handles serialization/deserialization of XP20 action tables to/from telegrams."""

    # Index constants for clarity in implementation
    SHORT_LONG_INDEX = 0
    GROUP_ON_OFF_INDEX = 1
    INVERT_INDEX = 2
    AND_FUNCTIONS_INDEX = 3  # starts at 3, uses indices 3-10
    SA_FUNCTION_INDEX = 11
    TA_FUNCTION_INDEX = 12

    @staticmethod
    def to_data(action_table: Xp20MsActionTable) -> str:
        """Serialize XP20 action table to telegram hex string format.

        Args:
            action_table: XP20 action table to serialize

        Returns:
            64-character hex string (32 bytes) with A-P nibble encoding
        """
        # Initialize 32-byte raw data array
        raw_bytes = bytearray(32)

        # Get all input channels
        input_channels = [
            action_table.input1,
            action_table.input2,
            action_table.input3,
            action_table.input4,
            action_table.input5,
            action_table.input6,
            action_table.input7,
            action_table.input8,
        ]

        # Encode each input channel
        for input_index, input_channel in enumerate(input_channels):
            Xp20MsActionTableSerializer._encode_input_channel(
                input_channel, input_index, raw_bytes
            )

        # Convert raw bytes to hex string with A-P encoding
        hex_data = ""
        for byte_val in raw_bytes:
            hex_data += nibble(byte_val)

        return hex_data

    @staticmethod
    def from_data(msactiontable_rawdata: str) -> Xp20MsActionTable:
        """Deserialize telegram data to XP20 action table.

        Args:
            msactiontable_rawdata: 64-character hex string with A-P encoding

        Returns:
            Decoded XP20 action table

        Raises:
            ValueError: If input length is not 64 characters
        """
        if len(msactiontable_rawdata) != 64:
            raise ValueError(
                f"XP20 action table data must be 64 characters long, got {len(msactiontable_rawdata)}"
            )

        # Convert hex string to bytes using de_nibble (A-P encoding)
        raw_bytes = de_nibble(msactiontable_rawdata)

        # Decode input channels
        input_channels = []
        for input_index in range(8):
            input_channel = Xp20MsActionTableSerializer._decode_input_channel(
                raw_bytes, input_index
            )
            input_channels.append(input_channel)

        # Create and return XP20 action table
        return Xp20MsActionTable(
            input1=input_channels[0],
            input2=input_channels[1],
            input3=input_channels[2],
            input4=input_channels[3],
            input5=input_channels[4],
            input6=input_channels[5],
            input7=input_channels[6],
            input8=input_channels[7],
        )

    @staticmethod
    def _decode_input_channel(raw_bytes: bytearray, input_index: int) -> InputChannel:
        """Extract input channel configuration from raw bytes.

        Args:
            raw_bytes: Raw byte array from telegram
            input_index: Input channel index (0-7)

        Returns:
            Decoded input channel configuration
        """
        # Extract bit flags from appropriate offsets
        short_long_flags = Xp20MsActionTableSerializer._byte_to_bits(
            raw_bytes[Xp20MsActionTableSerializer.SHORT_LONG_INDEX]
        )
        group_on_off_flags = Xp20MsActionTableSerializer._byte_to_bits(
            raw_bytes[Xp20MsActionTableSerializer.GROUP_ON_OFF_INDEX]
        )
        invert_flags = Xp20MsActionTableSerializer._byte_to_bits(
            raw_bytes[Xp20MsActionTableSerializer.INVERT_INDEX]
        )
        sa_function_flags = Xp20MsActionTableSerializer._byte_to_bits(
            raw_bytes[Xp20MsActionTableSerializer.SA_FUNCTION_INDEX]
        )
        ta_function_flags = Xp20MsActionTableSerializer._byte_to_bits(
            raw_bytes[Xp20MsActionTableSerializer.TA_FUNCTION_INDEX]
        )

        # Extract AND functions for this input (full byte)
        and_functions_byte = raw_bytes[
            Xp20MsActionTableSerializer.AND_FUNCTIONS_INDEX + input_index
        ]
        and_functions = Xp20MsActionTableSerializer._byte_to_bits(and_functions_byte)

        # Create and return input channel
        return InputChannel(
            invert=invert_flags[input_index],
            short_long=short_long_flags[input_index],
            group_on_off=group_on_off_flags[input_index],
            and_functions=and_functions,
            sa_function=sa_function_flags[input_index],
            ta_function=ta_function_flags[input_index],
        )

    @staticmethod
    def _encode_input_channel(
        input_channel: InputChannel, input_index: int, raw_bytes: bytearray
    ) -> None:
        """Encode input channel configuration into raw bytes.

        Args:
            input_channel: Input channel configuration to encode
            input_index: Input channel index (0-7)
            raw_bytes: Raw byte array to modify
        """
        # Set bit flags at appropriate positions
        if input_channel.short_long:
            raw_bytes[Xp20MsActionTableSerializer.SHORT_LONG_INDEX] |= 1 << input_index

        if input_channel.group_on_off:
            raw_bytes[Xp20MsActionTableSerializer.GROUP_ON_OFF_INDEX] |= (
                1 << input_index
            )

        if input_channel.invert:
            raw_bytes[Xp20MsActionTableSerializer.INVERT_INDEX] |= 1 << input_index

        if input_channel.sa_function:
            raw_bytes[Xp20MsActionTableSerializer.SA_FUNCTION_INDEX] |= 1 << input_index

        if input_channel.ta_function:
            raw_bytes[Xp20MsActionTableSerializer.TA_FUNCTION_INDEX] |= 1 << input_index

        # Encode AND functions (ensure we have exactly 8 bits)
        and_functions = input_channel.and_functions or [False] * 8
        and_functions_byte = 0
        for bit_index, bit_value in enumerate(
            and_functions[:8]
        ):  # Take only first 8 bits
            if bit_value:
                and_functions_byte |= 1 << bit_index

        raw_bytes[Xp20MsActionTableSerializer.AND_FUNCTIONS_INDEX + input_index] = (
            and_functions_byte
        )

    @staticmethod
    def _byte_to_bits(byte_value: int) -> list[bool]:
        """Convert a byte value to 8-bit boolean array.

        Args:
            byte_value: Byte value to convert

        Returns:
            List of 8 boolean values representing the bits
        """
        return [(byte_value & (1 << n)) != 0 for n in range(8)]

    @staticmethod
    def from_telegrams(ms_telegrams: str) -> Xp20MsActionTable:
        """Legacy method for backward compatibility. Use from_data() instead.

        Args:
            ms_telegrams: Full telegram string

        Returns:
            Decoded XP20 action table
        """
        # Extract data portion from telegram (skip header, take action table data)
        # Based on XP24 pattern: telegram[16:84] gives us the 68-char data portion
        # For XP20, we need 64 chars, so we take the first 64 chars after removing count
        data_parts = ms_telegrams[16:84]

        # Remove action table count (first 4 chars: AAAA, AAAB, etc.)
        hex_data = data_parts[4:68]  # Take 64 chars after count

        return Xp20MsActionTableSerializer.from_data(hex_data)
