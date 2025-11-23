"""Unit tests for XP24 Action Table short format."""

import pytest

from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam


class TestXp24ShortFormat:
    """Test cases for XP24 action table short format conversion."""

    def test_to_short_format_basic(self):
        """Test basic conversion to short format."""
        action_table = Xp24MsActionTable(
            input1_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.T05SEC
            ),
            input2_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.T1SEC
            ),
            input3_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input4_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
        )

        assert action_table.to_short_format() == [
            "T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12"
        ]

    def test_to_short_format_with_settings(self):
        """Test conversion to short format with settings."""
        short = Xp24MsActionTable(
            input1_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input2_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input3_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input4_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            mutex12=True,
            mutex34=True,
            curtain12=False,
            curtain34=False,
            mutual_deadtime=20,
        ).to_short_format()
        assert short == ["T:0 T:0 T:0 T:0 | M12:1 M34:1 C12:0 C34:0 DT:20"]

    def test_to_short_format_mixed_actions(self):
        """Test conversion with mixed action types."""
        short = Xp24MsActionTable(
            input1_action=InputAction(type=InputActionType.ON, param=TimeParam.T5SEC),
            input2_action=InputAction(type=InputActionType.OFF, param=TimeParam.NONE),
            input3_action=InputAction(
                type=InputActionType.LEVELSET, param=TimeParam.T5MIN
            ),
            input4_action=InputAction(
                type=InputActionType.SCENESET, param=TimeParam.T2MIN
            ),
        ).to_short_format()
        assert short == ["ON:4 OF:0 LS:12 SS:11 | M12:0 M34:0 C12:0 C34:0 DT:12"]

    def test_to_short_format_all_void(self):
        """Test conversion with all VOID actions."""
        short = Xp24MsActionTable(
            input1_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            input2_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            input3_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
            input4_action=InputAction(type=InputActionType.VOID, param=TimeParam.NONE),
        ).to_short_format()
        assert short == ["V:0 V:0 V:0 V:0 | M12:0 M34:0 C12:0 C34:0 DT:12"]

    def test_from_short_format_basic(self):
        """Test parsing basic short format."""
        short = "T:1 T:2 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12"
        action_table = Xp24MsActionTable.from_short_format([short])

        assert action_table.input1_action.type == InputActionType.TOGGLE
        assert action_table.input1_action.param == TimeParam.T05SEC
        assert action_table.input2_action.type == InputActionType.TOGGLE
        assert action_table.input2_action.param == TimeParam.T1SEC
        assert action_table.input3_action.type == InputActionType.TOGGLE
        assert action_table.input3_action.param == TimeParam.NONE
        assert action_table.input4_action.type == InputActionType.TOGGLE
        assert action_table.input4_action.param == TimeParam.NONE

    def test_from_short_format_with_settings(self):
        """Test parsing short format with settings."""
        short = "T:0 T:0 T:0 T:0 | M12:1 M34:1 C12:0 C34:0 DT:20"
        action_table = Xp24MsActionTable.from_short_format([short])

        assert action_table.mutex12 is True
        assert action_table.mutex34 is True
        assert action_table.curtain12 is False
        assert action_table.curtain34 is False
        assert action_table.mutual_deadtime == 20

    def test_from_short_format_mixed_actions(self):
        """Test parsing mixed action types."""
        short = "ON:4 OF:0 LS:12 SS:11 | M12:0 M34:0 C12:0 C34:0 DT:12"
        action_table = Xp24MsActionTable.from_short_format([short])

        assert action_table.input1_action.type == InputActionType.ON
        assert action_table.input1_action.param == TimeParam.T5SEC
        assert action_table.input2_action.type == InputActionType.OFF
        assert action_table.input2_action.param == TimeParam.NONE
        assert action_table.input3_action.type == InputActionType.LEVELSET
        assert action_table.input3_action.param == TimeParam.T5MIN
        assert action_table.input4_action.type == InputActionType.SCENESET
        assert action_table.input4_action.param == TimeParam.T2MIN

    def test_round_trip_conversion(self):
        """Test that converting to short and back preserves data."""
        original = Xp24MsActionTable(
            input1_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.T05SEC
            ),
            input2_action=InputAction(type=InputActionType.ON, param=TimeParam.T5SEC),
            input3_action=InputAction(
                type=InputActionType.LEVELSET, param=TimeParam.T5MIN
            ),
            input4_action=InputAction(
                type=InputActionType.SCENESET, param=TimeParam.T2MIN
            ),
            mutex12=True,
            mutex34=False,
            curtain12=True,
            curtain34=False,
            mutual_deadtime=20,
        )

        short = original.to_short_format()
        restored = Xp24MsActionTable.from_short_format(short)

        assert restored == original

    def test_from_short_format_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid short format"):
            Xp24MsActionTable.from_short_format(
                ["INVALID | M12:0 M34:0 C12:0 C34:0 DT:12"]
            )

    def test_from_short_format_invalid_action_code(self):
        """Test that invalid action code raises ValueError."""
        with pytest.raises(ValueError, match="Unknown action code"):
            Xp24MsActionTable.from_short_format(
                ["XX:0 T:0 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12"]
            )

    def test_from_short_format_invalid_param(self):
        """Test that invalid param raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time param"):
            Xp24MsActionTable.from_short_format(
                ["T:999 T:0 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12"]
            )

    def test_from_short_format_missing_colon(self):
        """Test that missing colon raises ValueError."""
        with pytest.raises(ValueError, match="Invalid action format"):
            Xp24MsActionTable.from_short_format(
                ["T1 T:0 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12"]
            )

    def test_all_action_types(self):
        """Test that all action types can be converted."""
        action_types = [
            (InputActionType.VOID, "V"),
            (InputActionType.ON, "ON"),
            (InputActionType.OFF, "OF"),
            (InputActionType.TOGGLE, "T"),
            (InputActionType.BLOCK, "BL"),
            (InputActionType.AUXRELAY, "AX"),
            (InputActionType.MUTUALEX, "MX"),
            (InputActionType.LEVELUP, "LU"),
            (InputActionType.LEVELDOWN, "LD"),
            (InputActionType.LEVELINC, "LI"),
            (InputActionType.LEVELDEC, "LC"),
            (InputActionType.LEVELSET, "LS"),
            (InputActionType.FADETIME, "FT"),
            (InputActionType.SCENESET, "SS"),
            (InputActionType.SCENENEXT, "SN"),
            (InputActionType.SCENEPREV, "SP"),
            (InputActionType.CTRLMETHOD, "CM"),
            (InputActionType.RETURNDATA, "RD"),
            (InputActionType.DELAYEDON, "DO"),
            (InputActionType.EVENTTIMER1, "E1"),
            (InputActionType.EVENTTIMER2, "E2"),
            (InputActionType.EVENTTIMER3, "E3"),
            (InputActionType.EVENTTIMER4, "E4"),
            (InputActionType.STEPCTRL, "SC"),
            (InputActionType.STEPCTRLUP, "SU"),
            (InputActionType.STEPCTRLDOWN, "SD"),
            (InputActionType.LEVELSETINTERN, "LN"),
            (InputActionType.FADE, "FD"),
            (InputActionType.LEARN, "LR"),
        ]

        for action_type, expected_code in action_types:
            action_table = Xp24MsActionTable(
                input1_action=InputAction(type=action_type, param=TimeParam.NONE),
            )
            short = action_table.to_short_format()
            assert short[0].startswith(f"{expected_code}:0 ")

            # Test round-trip
            restored = Xp24MsActionTable.from_short_format(short)
            assert restored.input1_action.type == action_type

    def test_all_time_params(self):
        """Test that all time param values can be converted."""
        time_params = [
            TimeParam.NONE,
            TimeParam.T05SEC,
            TimeParam.T1SEC,
            TimeParam.T2SEC,
            TimeParam.T5SEC,
            TimeParam.T10SEC,
            TimeParam.T15SEC,
            TimeParam.T20SEC,
            TimeParam.T30SEC,
            TimeParam.T45SEC,
            TimeParam.T1MIN,
            TimeParam.T2MIN,
            TimeParam.T5MIN,
            TimeParam.T10MIN,
            TimeParam.T15MIN,
            TimeParam.T20MIN,
            TimeParam.T30MIN,
            TimeParam.T45MIN,
            TimeParam.T60MIN,
            TimeParam.T120MIN,
        ]

        for time_param in time_params:
            action_table = Xp24MsActionTable(
                input1_action=InputAction(
                    type=InputActionType.TOGGLE, param=time_param
                ),
            )
            short = action_table.to_short_format()
            assert short == (
                [f"T:{time_param.value} T:0 T:0 T:0 | M12:0 M34:0 C12:0 C34:0 DT:12"]
            )

            # Test round-trip
            restored = Xp24MsActionTable.from_short_format(short)
            assert restored.input1_action.param == time_param
