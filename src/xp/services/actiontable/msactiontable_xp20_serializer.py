"""Serializer for XP20 Action Table telegram encoding/decoding."""

from xp.models.actiontable.msactiontable_xp20 import InputChannel, Xp20MsActionTable
from xp.utils.serialization import byte_to_bits, de_nibbles, nibbles

# Index constants for clarity in implementation
SHORT_LONG_INDEX: int = 0
GROUP_ON_OFF_INDEX: int = 1
INVERT_INDEX: int = 2
AND_FUNCTIONS_INDEX: int = 3  # starts at 3, uses indices 3-10
SA_FUNCTION_INDEX: int = 11
TA_FUNCTION_INDEX: int = 12


class Xp20MsActionTableSerializer:
    """Handles serialization/deserialization of XP20 action tables to/from telegrams."""

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

        encoded_data = nibbles(raw_bytes)
        # Convert raw bytes to hex string with A-P encoding
        return "AAAA" + encoded_data

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
        raw_length = len(msactiontable_rawdata)
        if raw_length < 68:  # Minimum: 4 char prefix + 64 chars data
            raise ValueError(
                f"XP20 action table data must be 68 characters long, got {len(msactiontable_rawdata)}"
            )

        # Remove action table count prefix (first 4 characters: AAAA, AAAB, etc.)
        data = msactiontable_rawdata[4:]

        # Take first 64 chars (32 bytes) as per pseudocode
        hex_data = data[:64]

        # Convert hex string to bytes using deNibble (A-P encoding)
        raw_bytes = de_nibbles(hex_data)

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
        short_long_flags = byte_to_bits(raw_bytes[SHORT_LONG_INDEX])
        group_on_off_flags = byte_to_bits(raw_bytes[GROUP_ON_OFF_INDEX])
        invert_flags = byte_to_bits(raw_bytes[INVERT_INDEX])
        sa_function_flags = byte_to_bits(raw_bytes[SA_FUNCTION_INDEX])
        ta_function_flags = byte_to_bits(raw_bytes[TA_FUNCTION_INDEX])

        # Extract AND functions for this input (full byte)
        and_functions_byte = raw_bytes[AND_FUNCTIONS_INDEX + input_index]
        and_functions = byte_to_bits(and_functions_byte)

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
            raw_bytes[SHORT_LONG_INDEX] |= 1 << input_index

        if input_channel.group_on_off:
            raw_bytes[GROUP_ON_OFF_INDEX] |= 1 << input_index

        if input_channel.invert:
            raw_bytes[INVERT_INDEX] |= 1 << input_index

        if input_channel.sa_function:
            raw_bytes[SA_FUNCTION_INDEX] |= 1 << input_index

        if input_channel.ta_function:
            raw_bytes[TA_FUNCTION_INDEX] |= 1 << input_index

        # Encode AND functions (ensure we have exactly 8 bits)
        and_functions = input_channel.and_functions or [False] * 8
        and_functions_byte = 0
        for bit_index, bit_value in enumerate(
            and_functions[:8]
        ):  # Take only first 8 bits
            if bit_value:
                and_functions_byte |= 1 << bit_index

        raw_bytes[AND_FUNCTIONS_INDEX + input_index] = and_functions_byte
