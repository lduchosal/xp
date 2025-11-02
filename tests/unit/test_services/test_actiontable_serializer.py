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
                    command=InputActionType.TURNOFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "CP20 0 0 > 1 TURNOFF;"

    def test_format_decoded_output_with_parameter(self):
        """Test formatting with non-zero parameter."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=2,
                    module_output=1,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.T1SEC,  # value = 2
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 2 > 1 TURNON 2;"

    def test_format_decoded_output_parameter_zero(self):
        """Test that parameter=0 is omitted from output."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.NONE,  # value = 0
                    inverted=False,
                )
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 0 > 1 TURNON;"
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
                    command=InputActionType.TURNON,
                    parameter=TimeParam.NONE,
                    inverted=True,
                )
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 0 1 > 1 ~TURNON;"

    def test_format_decoded_output_inverted_with_parameter(self):
        """Test inverted command with parameter."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=1,
                    module_input=2,
                    module_output=3,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.T5SEC,  # value = 4
                    inverted=True,
                )
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 1
        assert result[0] == "CP20 1 2 > 3 ~TURNON 4;"

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
                    command=InputActionType.TURNOFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=2,
                    command=InputActionType.TURNOFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=1,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.NONE,
                    inverted=True,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=2,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        assert len(result) == 4
        assert result[0] == "CP20 0 0 > 1 TURNOFF;"
        assert result[1] == "CP20 0 0 > 2 TURNOFF;"
        assert result[2] == "CP20 0 1 > 1 ~TURNON;"
        assert result[3] == "CP20 0 1 > 2 TURNON;"

    def test_format_decoded_output_semicolon(self):
        """Test that all entries end with semicolon."""
        action_table = ActionTable(
            entries=[
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=1,
                    command=InputActionType.TURNOFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=2,
                    command=InputActionType.TURNON,
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
                    command=InputActionType.TURNOFF,
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
                    command=InputActionType.TURNOFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=0,
                    module_output=2,
                    command=InputActionType.TURNOFF,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=1,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.NONE,
                    inverted=True,
                ),
                ActionTableEntry(
                    module_type=ModuleTypeCode.CP20,
                    link_number=0,
                    module_input=1,
                    module_output=2,
                    command=InputActionType.TURNON,
                    parameter=TimeParam.NONE,
                    inverted=False,
                ),
            ]
        )

        result = ActionTableSerializer.format_decoded_output(action_table)

        expected = [
            "CP20 0 0 > 1 TURNOFF;",
            "CP20 0 0 > 2 TURNOFF;",
            "CP20 0 1 > 1 ~TURNON;",
            "CP20 0 1 > 2 TURNON;",
        ]
        assert result == expected
