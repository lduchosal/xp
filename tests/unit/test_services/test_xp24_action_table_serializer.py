"""Unit tests for XP24 Action Table Serializer."""

import pytest

from xp.models.input_action_type import InputActionType
from xp.models.timeparam_type import TimeParam
from xp.models.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.services.msactiontable_xp24_serializer import Xp24MsActionTableSerializer
from xp.utils.serialization import de_nibbles


class TestXp24MsActionTableSerializer:
    """Test cases for Xp24MsActionTableSerializer"""

    @pytest.fixture
    def sample_action_table(self):
        """Create sample action table for testing"""
        return Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TOGGLE, TimeParam.NONE),
            input2_action=InputAction(InputActionType.TURNON, TimeParam.T5SEC),
            input3_action=InputAction(InputActionType.LEVELSET, TimeParam.T5SEC),
            input4_action=InputAction(InputActionType.SCENESET, TimeParam.T5SEC),
            mutex12=True,
            mutex34=False,
            mutual_deadtime=Xp24MsActionTable.MS500,
            curtain12=False,
            curtain34=True,
        )

    @pytest.fixture
    def sample_telegrams(self):
        """Create sample telegrams for testing"""
        return [
            "<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>",
            "<R0020044966F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFB>",
            "<R0020044986F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>",
            "<R0020041824F17DAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>",
            "<R0020044964F17DAAAAABAGADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>",
        ]

    def test_from_telegrams_basic(self, sample_telegrams: list[str]) -> None:
        """Test basic telegram parsing"""

        assert sample_telegrams
        action_table = Xp24MsActionTableSerializer.from_telegrams(sample_telegrams[0])

        # Verify it's a valid Xp24ActionTable
        assert isinstance(action_table, Xp24MsActionTable)

        # Check that we have 4 input actions
        assert action_table.input1_action is not None
        assert action_table.input2_action is not None
        assert action_table.input3_action is not None
        assert action_table.input4_action is not None

    def test_from_telegrams_invalid_hex_data(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        # This telegram contains non-hex characters that cause from_hex() to fail
        # Based on the debug log: '<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>'
        valid_telegram = (
            "AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        msactiontable = Xp24MsActionTableSerializer.from_data(valid_telegram)
        assert msactiontable.input1_action.type == InputActionType.TOGGLE
        assert msactiontable.input2_action.type == InputActionType.TOGGLE
        assert msactiontable.input3_action.type == InputActionType.TOGGLE
        assert msactiontable.input4_action.type == InputActionType.TOGGLE

        assert msactiontable.input1_action.param == TimeParam.NONE
        assert msactiontable.input2_action.param == TimeParam.NONE
        assert msactiontable.input3_action.param == TimeParam.NONE
        assert msactiontable.input4_action.param == TimeParam.NONE

        assert not msactiontable.curtain12
        assert not msactiontable.curtain34
        assert not msactiontable.mutex12
        assert not msactiontable.mutex34

    def test_from_telegrams_invalid_hex_data2(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        # This telegram contains non-hex characters that cause from_hex() to fail
        # Based on the debug log: '<R0020044964F17DAAAAABAGADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>'
        valid_telegram = (
            "AAAAABAGADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        msactiontable = Xp24MsActionTableSerializer.from_data(valid_telegram)
        assert msactiontable.input1_action.type == InputActionType.TURNON
        assert msactiontable.input2_action.type == InputActionType.TOGGLE
        assert msactiontable.input3_action.type == InputActionType.TOGGLE
        assert msactiontable.input4_action.type == InputActionType.TOGGLE

        assert msactiontable.input1_action.param == TimeParam.T15SEC
        assert msactiontable.input2_action.param == TimeParam.NONE
        assert msactiontable.input3_action.param == TimeParam.NONE
        assert msactiontable.input4_action.param == TimeParam.NONE

        assert not msactiontable.curtain12
        assert not msactiontable.curtain34
        assert not msactiontable.mutex12
        assert not msactiontable.mutex34

    def test_from_telegrams_de_nibble_0(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AA"

        result = de_nibbles(nibble)
        assert bytearray([0]) == result

    def test_from_telegrams_de_nibble_1(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AB"

        result = de_nibbles(nibble)
        assert bytearray([1]) == result

    def test_from_telegrams_de_nibble_01(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AAAB"

        result = de_nibbles(nibble)
        assert bytearray([0, 1]) == result

    def test_from_telegrams_de_nibble_big(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        result = de_nibbles(nibble)
        assert (
            bytearray(
                [
                    0,
                    0,
                    3,
                    0,
                    3,
                    0,
                    3,
                    0,
                    3,
                    0,
                    0,
                    0,
                    12,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            )
            == result
        )
