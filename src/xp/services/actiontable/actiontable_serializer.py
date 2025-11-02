"""Serializer for ActionTable telegram encoding/decoding."""

import re

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.utils.serialization import (
    byte_to_unsigned,
    de_bcd,
    de_nibbles,
    highest_bit_set,
    lower3,
    nibbles,
    remove_highest_bit,
    to_bcd,
    upper5,
)


class ActionTableSerializer:
    """Handles serialization/deserialization of ActionTable to/from telegrams.

    Attributes:
        MAX_ENTRIES: Maximum number of entries in an ActionTable (96).
    """

    MAX_ENTRIES = 96  # ActionTable must always contain exactly 96 entries

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
                module_type = ModuleTypeCode.NOMOD  # Default fallback

            try:
                command = InputActionType(command_raw)
            except ValueError:
                command = InputActionType.OFF  # Default fallback

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
            Raw byte data for telegram (always 480 bytes for 96 entries)
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

        # Pad to 96 entries with default NOMOD entries (00 00 00 00 00)
        current_entries = len(action_table.entries)
        if current_entries < ActionTableSerializer.MAX_ENTRIES:
            # Default entry: NOMOD 0 0 > 0 OFF (all zeros)
            padding_bytes = [0x00, 0x00, 0x00, 0x00, 0x00]
            for _ in range(ActionTableSerializer.MAX_ENTRIES - current_entries):
                data.extend(padding_bytes)

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
    def format_decoded_output(action_table: ActionTable) -> list[str]:
        """Format ActionTable as human-readable decoded output.

        Args:
            action_table: ActionTable to format

        Returns:
            List of human-readable string representations
        """
        lines = []
        for entry in action_table.entries:
            # Format: CP20 0 0 > 1 OFF [param];
            module_type = entry.module_type.name
            link = entry.link_number
            input_num = entry.module_input
            output = entry.module_output
            command = entry.command.name

            # Add prefix for inverted commands
            if entry.inverted:
                command = f"~{command}"

            # Build base line
            line = f"{module_type} {link} {input_num} > {output} {command}"

            # Add parameter if present and non-zero
            if entry.parameter is not None and entry.parameter.value != 0:
                line += f" {entry.parameter.value}"

            # Add semicolon terminator
            line += ";"

            lines.append(line)

        return lines

    @staticmethod
    def parse_action_string(action_str: str) -> ActionTableEntry:
        """Parse action table entry from string format.

        Args:
            action_str: String in format "CP20 0 0 > 1 OFF" or "CP20 0 1 > 1 ~ON"

        Returns:
            Parsed ActionTableEntry

        Raises:
            ValueError: If string format is invalid
        """
        # Remove trailing semicolon if present
        action_str = action_str.strip().rstrip(";")

        # Pattern: <Type> <Link> <Input> > <Output> <Command> [Parameter]
        pattern = r"^(\w+)\s+(\d+)\s+(\d+)\s+>\s+(\d+)\s+(~?)(\w+)(?:\s+(\d+))?$"
        match = re.match(pattern, action_str)

        if not match:
            raise ValueError(f"Invalid action table format: {action_str}")

        (
            module_type_str,
            link_str,
            input_str,
            output_str,
            inverted_str,
            command_str,
            parameter_str,
        ) = match.groups()

        # Parse module type
        try:
            module_type = ModuleTypeCode[module_type_str]
        except KeyError:
            raise ValueError(f"Invalid module type: {module_type_str}")

        # Parse command
        try:
            command = InputActionType[command_str]
        except KeyError:
            raise ValueError(f"Invalid command: {command_str}")

        # Parse parameter (default to NONE)
        parameter = TimeParam.NONE
        if parameter_str:
            try:
                parameter = TimeParam(int(parameter_str))
            except ValueError:
                raise ValueError(f"Invalid parameter: {parameter_str}")

        return ActionTableEntry(
            module_type=module_type,
            link_number=int(link_str),
            module_input=int(input_str),
            module_output=int(output_str),
            command=command,
            parameter=parameter,
            inverted=bool(inverted_str),
        )

    @staticmethod
    def parse_action_table(action_strings: list[str]) -> ActionTable:
        """Parse action table from list of string entries.

        Args:
            action_strings: List of action strings from conson.yml

        Returns:
            Parsed ActionTable
        """
        entries = [
            ActionTableSerializer.parse_action_string(action_str)
            for action_str in action_strings
        ]
        return ActionTable(entries=entries)
