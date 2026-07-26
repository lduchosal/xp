# Copyright (c) 2025 ldvchosal
"""Unit tests for ActionTableSerializer format_decoded_output."""

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.utils.serialization import de_nibbles

# 96 entries x 5 bytes x 2 nibbles
ENCODED_TABLE_LENGTH = 960
# 96 entries x 5 bytes
DECODED_TABLE_LENGTH = 480
# Number of OFF entries in the typical 8-entry configuration
OFF_ENTRY_COUNT = 4


class TestActionTableSerializerFormatDecoded:
    """Test cases for ActionTableSerializer format_decoded_output."""

    def test_format_decoded_output_basic(self) -> None:
        """Test basic formatting without parameters."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "CP20 0 0 > 1 OFF;"

    def test_format_decoded_output_with_parameter(self) -> None:
        """Test formatting with non-zero parameter."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=2,
                    module_output=1,
                    command=InputActionType.ON,
                    parameter=TimeParam.T1SEC,  # value = 2
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 2 > 1 ON 2;"

    def test_format_decoded_output_parameter_zero(self) -> None:
        """Test that parameter=0 is omitted from output."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,  # value = 0
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 0 > 1 ON;"
        assert " 0;" not in result[0]

    def test_format_decoded_output_inverted(self) -> None:
        """Test inverted command with ~ prefix."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=1,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,
                    inverted=True,
                )
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 1 > 1 ~ON;"

    def test_format_decoded_output_inverted_with_parameter(self) -> None:
        """Test inverted command with parameter."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=1,
                    module_input=2,
                    module_output=3,
                    command=InputActionType.ON,
                    parameter=TimeParam.T5SEC,  # value = 4
                    inverted=True,
                )
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 1 2 > 3 ~ON 4;"

    def test_format_decoded_output_empty(self) -> None:
        """Test formatting empty action table."""
        action_table = ActionTable(entries=[])

        result = ActionTableSerializer.to_short_string(action_table)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_decoded_output_multiple_entries(self) -> None:
        """Test formatting multiple entries."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=2,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=1,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,
                    inverted=True,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=2,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert len(result) == len(action_table.entries)
        assert result[0] == "CP20 0 0 > 1 OFF;"
        assert result[1] == "CP20 0 0 > 2 OFF;"
        assert result[2] == "CP20 0 1 > 1 ~ON;"
        assert result[3] == "CP20 0 1 > 2 ON;"

    def test_format_decoded_output_semicolon(self) -> None:
        """Test that all entries end with semicolon."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=2,
                    command=InputActionType.ON,
                    parameter=TimeParam.T1SEC,
                    inverted=True,
                ),
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert all(line.endswith(";") for line in result)

    def test_format_decoded_output_returns_list(self) -> None:
        """Test that format_decoded_output returns a list, not a string."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        assert isinstance(result, list)

    def test_format_decoded_output_spec_example(self) -> None:
        """Test formatting matches specification example."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=2,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=1,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,
                    inverted=True,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=2,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
            ]
        )

        result = ActionTableSerializer.to_short_string(action_table)

        expected = [
            "CP20 0 0 > 1 OFF;",
            "CP20 0 0 > 2 OFF;",
            "CP20 0 1 > 1 ~ON;",
            "CP20 0 1 > 2 ON;",
        ]
        assert result == expected


class TestActionTableSerializerPadding:
    """Test cases for ActionTableSerializer 96-entry padding."""

    def test_to_data_pads_to_96_entries(self) -> None:
        """Test that to_data pads to exactly 96 entries (480 bytes)."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.to_encoded_string(action_table)

        # Should be exactly 960 characters (96 entries x 5 bytes x 2 nibbles)
        assert len(result) == ENCODED_TABLE_LENGTH

    def test_to_data_padding_with_multiple_entries(self) -> None:
        """Test padding with 8 entries (typical configuration)."""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=i // 4,
                module_output=(i % 4) + 1,
                command=InputActionType.OFF
                if i < OFF_ENTRY_COUNT
                else InputActionType.ON,
                parameter=TimeParam.NONE,
                inverted=False,
            )
            for i in range(8)
        ]
        action_table = ActionTable(entries=entries)

        encoded_string = ActionTableSerializer.to_encoded_string(action_table)
        result = de_nibbles(encoded_string)

        # Should still be exactly 480 bytes
        assert len(result) == DECODED_TABLE_LENGTH

        # First 40 bytes (8 entries x 5 bytes) should contain actual data
        # Remaining 440 bytes should be padding (all zeros)
        assert result[40:] == b"\x00" * 440

    def test_to_data_padding_bytes_are_zeros(self) -> None:
        """Test that padding bytes are all zeros (NOMOD default entry)."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.OFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        encoded_string = ActionTableSerializer.to_encoded_string(action_table)
        result = de_nibbles(encoded_string)

        # First 5 bytes are the actual entry
        # Remaining bytes (5 to 480) should all be zeros
        assert result[5:] == b"\x00" * 475

    def test_to_data_no_padding_needed_for_96_entries(self) -> None:
        """Test that exactly 96 entries don't get extra padding."""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=0,
                module_output=1,
                command=InputActionType.OFF,
                parameter=TimeParam.NONE,
                inverted=False,
            )
            for _ in range(96)
        ]
        action_table = ActionTable(entries=entries)

        result = ActionTableSerializer.to_encoded_string(action_table)

        # Should be exactly 960 characters (480 bytes nibble-encoded)
        assert len(result) == ENCODED_TABLE_LENGTH

    def test_to_data_padding_preserves_actual_entries(self) -> None:
        """Test that padding doesn't corrupt actual entry data."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,  # value=2 -> 0x02 in BCD
                    link_number=1,  # 0x01
                    module_input=2,  # 0x02
                    module_output=3,  # bits 0-2
                    command=InputActionType.ON,  # 0x01, bits 3-7
                    parameter=TimeParam.T5SEC,  # 0x04
                    inverted=False,
                )
            ]
        )

        encoded_string = ActionTableSerializer.to_encoded_string(action_table)
        result = de_nibbles(encoded_string)

        # Check first entry is correct (5 bytes): module type CP20 in BCD,
        # link number, module input,
        # output byte with 0-indexed output ((3-1) | (ON << 3) = 2 | 8 = 10),
        # and parameter
        assert result[:5] == bytes([0x02, 0x01, 0x02, 0x0A, 0x04])

        # Rest should be padding
        assert result[5:] == b"\x00" * 475

    def test_to_data_empty_action_table(self) -> None:
        """Test that empty action table is padded to 96 entries."""
        action_table = ActionTable(entries=[])

        encoded_string = ActionTableSerializer.to_encoded_string(action_table)
        result = de_nibbles(encoded_string)

        # Should still be 480 bytes, all zeros
        assert len(result) == DECODED_TABLE_LENGTH
        assert result == b"\x00" * 480

    def test_to_encoded_string_cp20_link4_input0_output1_on(self) -> None:
        """Test encoding CP20 4 0 > 1 ON produces expected BCD string.

        ActionTable: CP20 4 0 > 1 ON;
        Serialized BCD (first 8 chars): ACAEAAAI
        """
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=4,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.ON,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        encoded_string = ActionTableSerializer.to_encoded_string(action_table)

        # First 8 characters (4 bytes in BCD, high-nibble first):
        # byte 0 "AC" is 0x02 (CP20, value 2)
        # byte 1 "AE" is 0x04 (link number 4)
        # byte 2 "AA" is 0x00 (module input 0)
        # byte 3 "AI" is 0x08 (output 0-indexed: (1-1) | (ON<<3) = 0 | 8 = 8)
        assert encoded_string[:8] == "ACAEAAAI"

    def test_from_encoded_string_cp20_link4_input0_output1_on(self) -> None:
        """Test decoding BCD string ACAEAAAI produces expected ActionTable.

        Serialized BCD: ACAEAAAI (+ padding)
        ActionTable: CP20 4 0 > 1 ON;
        """
        # Build full 960-char encoded string (96 entries x 5 bytes x 2 nibbles)
        # First entry: ACAEAAAI, rest is padding (AA = 0x00)
        encoded_string = "ACAEAAAI" + "AA" * 476

        action_table = ActionTableSerializer.from_encoded_string(encoded_string)

        # Should have exactly 1 entry (padding entries with NOMOD are filtered out)
        assert len(action_table.entries) == 1

        # module_output is 0-indexed in wire format, converted to 1
        assert action_table.entries[0] == ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=4,
            module_input=0,
            module_output=1,
            command=InputActionType.ON,
            parameter=TimeParam.NONE,
            inverted=False,
        )

    def test_to_encoded_string_cp20_link13_input9_output1_levelinc(self) -> None:
        """Test encoding CP20 13 9 > 1 LEVELINC produces expected BCD string.

        ActionTable: CP20 13 9 > 1 LEVELINC;
        Serialized BCD (first 8 chars): ACBDAJEI
        """
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=13,
                    module_input=9,
                    module_output=1,
                    command=InputActionType.LEVELINC,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        encoded_string = ActionTableSerializer.to_encoded_string(action_table)

        # First 8 characters (4 bytes in BCD, high-nibble first):
        # byte 0 "AC" is 0x02 (CP20, value 2)
        # byte 1 "BD" is 0x13 (link number 13 in BCD)
        # byte 2 "AJ" is 0x09 (module input 9)
        # byte 3 "EI" is 0x48 (output 0-indexed: (1-1) | (LEVELINC<<3) = 0 | 72)
        assert encoded_string[:8] == "ACBDAJEI"

    def test_from_encoded_string_cp20_link13_input9_output1_levelinc(self) -> None:
        """Test decoding BCD string ACBDAJEIAA produces expected ActionTable.

        Serialized BCD: ACBDAJEIAA (+ padding)
        ActionTable: CP20 13 9 > 1 LEVELINC;
        """
        # Build full 960-char encoded string (96 entries x 5 bytes x 2 nibbles)
        # First entry: ACBDAJEIAA, rest is padding (AA = 0x00)
        encoded_string = "ACBDAJEIAA" + "AA" * 475

        action_table = ActionTableSerializer.from_encoded_string(encoded_string)

        # Should have exactly 1 entry (padding entries with NOMOD are filtered out)
        assert len(action_table.entries) == 1

        # module_output is 0-indexed in wire format, converted to 1
        assert action_table.entries[0] == ActionTableEntry(
            module_type=ModuleTypeCode.CP20,
            link_number=13,
            module_input=9,
            module_output=1,
            command=InputActionType.LEVELINC,
            parameter=TimeParam.NONE,
            inverted=False,
        )
