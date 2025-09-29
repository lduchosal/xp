"""Serializer for ActionTable telegram encoding/decoding."""

from ..models.actiontable import ActionTable, ActionTableEntry
from ..models import ModuleTypeCode
from ..models.input_action_type import InputActionType
from ..models.timeparam_type import TimeParam
from ..utils.serialization import (
    de_bcd,
    to_bcd,
    lower3,
    upper5,
    de_nibbles,
    nibbles,
    byte_to_unsigned,
    remove_highest_bit,
    highest_bit_set,
)


class ActionTableSerializer:
    """Handles serialization/deserialization of ActionTable to/from telegrams."""

    @staticmethod
    def from_data(data: bytes) -> ActionTable:
        """Deserialize telegram data to ActionTable.

        Args:
            data: Raw byte data from telegram

        Returns:
            Decoded ActionTable
        """
        entries = []

        # Process data in 5-byte chunks
        for i in range(0, len(data), 5):
            if i + 4 >= len(data):
                break

            # Extract fields from 5-byte chunk
            module_type_raw = de_bcd(data[i])
            link_number = de_bcd(data[i + 1])
            module_input = de_bcd(data[i + 2])

            # Extract output and command from byte 3
            module_output = lower3(data[i + 3])
            command_raw = upper5(data[i + 3])

            parameter_raw = byte_to_unsigned(data[i + 4])
            parameter_raw = remove_highest_bit(parameter_raw)

            inverted = False
            if highest_bit_set(data[i + 4]):
                inverted = True

            # Map raw values to enum types
            try:
                module_type = ModuleTypeCode(module_type_raw)
            except ValueError:
                module_type = ModuleTypeCode.CP20  # Default fallback

            try:
                command = InputActionType(command_raw)
            except ValueError:
                command = InputActionType.TURNOFF  # Default fallback

            try:
                parameter = TimeParam(parameter_raw)
            except ValueError:
                parameter = TimeParam.NONE  # Default fallback

            if module_type != ModuleTypeCode.NOMOD:
                entry = ActionTableEntry(
                    module_type=module_type,
                    link_number=link_number,
                    module_input=module_input,
                    module_output=module_output,
                    command=command,
                    parameter=parameter,
                    inverted=inverted,
                )
                entries.append(entry)

        return ActionTable(entries=entries)

    @staticmethod
    def to_data(action_table: ActionTable) -> bytes:
        """Serialize ActionTable to telegram byte data.

        Args:
            action_table: ActionTable to serialize

        Returns:
            Raw byte data for telegram
        """
        data = bytearray()

        for entry in action_table.entries:
            # Encode each entry as 5 bytes
            type_byte = to_bcd(entry.module_type.value)
            link_byte = to_bcd(entry.link_number)
            input_byte = to_bcd(entry.module_input)

            # Combine output (lower 3 bits) and command (upper 5 bits)
            output_command_byte = (entry.module_output & 0x07) | (
                (entry.command.value & 0x1F) << 3
            )

            parameter_byte = entry.parameter.value

            data.extend(
                [type_byte, link_byte, input_byte, output_command_byte, parameter_byte]
            )

        return bytes(data)

    @staticmethod
    def to_encoded_string(action_table: ActionTable) -> str:
        """Convert ActionTable to base64-encoded string format.

        Args:
            action_table: ActionTable to encode

        Returns:
            Base64-encoded string representation
        """
        data = ActionTableSerializer.to_data(action_table)
        return nibbles(data)

    @staticmethod
    def from_encoded_string(encoded_data: str) -> ActionTable:
        """Convert base64-encoded string to ActionTable.

        Args:
            encoded_data: Base64-encoded string

        Returns:
            Decoded ActionTable
        """
        data = de_nibbles(encoded_data)
        return ActionTableSerializer.from_data(data)

    @staticmethod
    def format_decoded_output(action_table: ActionTable) -> str:
        """Format ActionTable as human-readable decoded output.

        Args:
            action_table: ActionTable to format

        Returns:
            Human-readable string representation
        """
        lines = []
        for entry in action_table.entries:
            # Format: CP20 0 0 > 1 OFF;
            module_type = entry.module_type.name
            link = entry.link_number
            input_num = entry.module_input
            output = entry.module_output
            command = entry.command.name

            # Add prefix for special commands
            if entry.inverted:
                command = f"~{command}"

            line = f"{module_type} {link} {input_num} > {output} {command};"
            lines.append(line)

        return "\n".join(lines)
