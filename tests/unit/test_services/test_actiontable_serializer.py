"""Unit tests for ActionTableSerializer format_decoded_output."""

from xp.models import ModuleTypeCode
from xp.models.actiontable.actiontable import ActionTable, ActionTableEntry
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer


class TestActionTableSerializerFormatDecoded:
    """Test cases for ActionTableSerializer format_decoded_output."""

    def test_format_decoded_output_basic(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "CP20 0 0 > 1 OFF;"

    def test_format_decoded_output_with_parameter(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 2 > 1 ON 2;"

    def test_format_decoded_output_parameter_zero(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 0 > 1 ON;"
        assert " 0;" not in result[0]

    def test_format_decoded_output_inverted(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 1 > 1 ~ON;"

    def test_format_decoded_output_inverted_with_parameter(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 1 2 > 3 ~ON 4;"

    def test_format_decoded_output_empty(self):
        """Test formatting empty action table."""
        action_table = ActionTable(entries=[])

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_decoded_output_multiple_entries(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 4
        assert result[0] == "CP20 0 0 > 1 OFF;"
        assert result[1] == "CP20 0 0 > 2 OFF;"
        assert result[2] == "CP20 0 1 > 1 ~ON;"
        assert result[3] == "CP20 0 1 > 2 ON;"

    def test_format_decoded_output_semicolon(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert all(line.endswith(";") for line in result)

    def test_format_decoded_output_returns_list(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert isinstance(result, list)

    def test_format_decoded_output_spec_example(self):
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

        result = ActionTableSerializer.format_decoded_output(action_table)

        expected = [
            "CP20 0 0 > 1 OFF;",
            "CP20 0 0 > 2 OFF;",
            "CP20 0 1 > 1 ~ON;",
            "CP20 0 1 > 2 ON;",
        ]
        assert result == expected


class TestActionTableSerializerPadding:
    """Test cases for ActionTableSerializer 96-entry padding."""

    def test_to_data_pads_to_96_entries(self):
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

        result = ActionTableSerializer.to_data(action_table)

        # Should be exactly 96 entries × 5 bytes = 480 bytes
        assert len(result) == 480

    def test_to_data_padding_with_multiple_entries(self):
        """Test padding with 8 entries (typical configuration)."""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=i // 4,
                module_output=(i % 4) + 1,
                command=InputActionType.OFF if i < 4 else InputActionType.ON,
                parameter=TimeParam.NONE,
                inverted=False,
            )
            for i in range(8)
        ]
        action_table = ActionTable(entries=entries)

        result = ActionTableSerializer.to_data(action_table)

        # Should still be exactly 480 bytes
        assert len(result) == 480

        # First 40 bytes (8 entries × 5 bytes) should contain actual data
        # Remaining 440 bytes should be padding (all zeros)
        assert result[40:] == b"\x00" * 440

    def test_to_data_padding_bytes_are_zeros(self):
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

        result = ActionTableSerializer.to_data(action_table)

        # First 5 bytes are the actual entry
        # Remaining bytes (5 to 480) should all be zeros
        assert result[5:] == b"\x00" * 475

    def test_to_data_no_padding_needed_for_96_entries(self):
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

        result = ActionTableSerializer.to_data(action_table)

        # Should be exactly 480 bytes, no more
        assert len(result) == 480

    def test_to_data_padding_preserves_actual_entries(self):
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

        result = ActionTableSerializer.to_data(action_table)

        # Check first entry is correct (5 bytes)
        assert result[0] == 0x02  # CP20 (value=2) in BCD
        assert result[1] == 0x01  # link_number
        assert result[2] == 0x02  # module_input
        assert result[3] == 0x0B  # output (3) | command (1 << 3)
        assert result[4] == 0x04  # parameter

        # Rest should be padding
        assert result[5:] == b"\x00" * 475

    def test_to_data_empty_action_table(self):
        """Test that empty action table is padded to 96 entries."""
        action_table = ActionTable(entries=[])

        result = ActionTableSerializer.to_data(action_table)

        # Should still be 480 bytes, all zeros
        assert len(result) == 480
        assert result == b"\x00" * 480
