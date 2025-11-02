"""Unit tests for XP24 Action Table models."""

from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


class TestInputAction:
    """Test cases for InputAction model."""

    def test_create_input_action_with_param(self):
        """Test creating InputAction with parameter."""
        action = InputAction(InputActionType.ON, TimeParam.T5SEC)

        assert action.type == InputActionType.ON
        assert action.param == TimeParam.T5SEC

    def test_create_input_action_without_param(self):
        """Test creating InputAction without parameter."""
        action = InputAction(InputActionType.TOGGLE, TimeParam.NONE)

        assert action.type == InputActionType.TOGGLE
        assert action.param == TimeParam.NONE

    def test_input_action_equality(self):
        """Test InputAction equality comparison."""
        action1 = InputAction(InputActionType.TOGGLE, TimeParam.NONE)
        action2 = InputAction(InputActionType.TOGGLE, TimeParam.NONE)
        action3 = InputAction(InputActionType.ON, TimeParam.T5SEC)

        assert action1 == action2
        assert action1 != action3


class TestXp24ActionTable:
    """Test cases for Xp24ActionTable model."""

    def test_create_xp24_action_table_with_defaults(self):
        """Test creating Xp24ActionTable with default values."""
        action_table = Xp24MsActionTable()

        # Verify default input actions are TOGGLE with None param
        assert action_table.input1_action.type == InputActionType.TOGGLE
        assert action_table.input1_action.param == TimeParam.NONE
        assert action_table.input2_action.type == InputActionType.TOGGLE
        assert action_table.input2_action.param == TimeParam.NONE
        assert action_table.input3_action.type == InputActionType.TOGGLE
        assert action_table.input3_action.param == TimeParam.NONE
        assert action_table.input4_action.type == InputActionType.TOGGLE
        assert action_table.input4_action.param == TimeParam.NONE

        # Verify default boolean settings
        assert action_table.mutex12 is False
        assert action_table.mutex34 is False
        assert action_table.curtain12 is False
        assert action_table.curtain34 is False

        # Verify default MS timing
        assert action_table.mutual_deadtime == Xp24MsActionTable.MS300

    def test_xp24_action_table_constants(self):
        """Test XP24 action table timing constants."""
        assert Xp24MsActionTable.MS300 == 12
        assert Xp24MsActionTable.MS500 == 20

    def test_xp24_action_table_equality(self):
        """Test Xp24ActionTable equality comparison."""
        action_table1 = Xp24MsActionTable()
        action_table2 = Xp24MsActionTable()
        action_table3 = Xp24MsActionTable(
            input1_action=InputAction(InputActionType.ON, TimeParam.T5SEC),
            mutex12=True,
        )

        assert action_table1 == action_table2
        assert action_table1 != action_table3

    def test_xp24_action_table_dataclass_fields(self):
        """Test that all expected fields are present in dataclass."""
        action_table = Xp24MsActionTable()

        # Check that all expected attributes exist
        assert hasattr(action_table, "input1_action")
        assert hasattr(action_table, "input2_action")
        assert hasattr(action_table, "input3_action")
        assert hasattr(action_table, "input4_action")
        assert hasattr(action_table, "mutex12")
        assert hasattr(action_table, "mutex34")
        assert hasattr(action_table, "curtain12")
        assert hasattr(action_table, "curtain34")
        assert hasattr(action_table, "mutual_deadtime")

    def test_input_action_type_enum_coverage(self):
        """Test that all major InputActionType enum values work."""
        # Test a selection of action types
        test_actions = [
            InputActionType.VOID,
            InputActionType.ON,
            InputActionType.OFF,
            InputActionType.TOGGLE,
            InputActionType.LEVELSET,
            InputActionType.SCENESET,
            InputActionType.LEARN,
        ]

        for action_type in test_actions:
            action = InputAction(action_type, TimeParam.NONE)
            assert action.type == action_type
            assert isinstance(action_type.value, int)

    def test_input_action_with_various_param_types(self):
        """Test InputAction with various parameter formats."""
        # Test with numeric string
        action1 = InputAction(InputActionType.LEVELSET, TimeParam.T60MIN)
        assert action1.param == TimeParam.T60MIN

        # Test with zero string
        action2 = InputAction(InputActionType.ON, TimeParam.NONE)
        assert action2.param == TimeParam.NONE

        # Test with None
        action3 = InputAction(InputActionType.TOGGLE, TimeParam.NONE)
        assert action3.param == TimeParam.NONE
