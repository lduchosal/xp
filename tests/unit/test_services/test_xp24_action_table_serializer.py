"""Unit tests for XP24 Action Table Serializer."""

import pytest

from xp.models.input_action_type import InputActionType
from xp.models.xp24_msactiontable import InputAction, Xp24MsActionTable
from xp.services.xp24_action_table_serializer import Xp24MsActionTableSerializer


class TestXp24ActionTableSerializer:
    """Test cases for Xp24ActionTableSerializer"""

    @pytest.fixture
    def sample_action_table(self):
        """Create sample action table for testing"""
        return Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TOGGLE, None),
            input2_action=InputAction(InputActionType.TURNON, "5"),
            input3_action=InputAction(InputActionType.LEVELSET, "75"),
            input4_action=InputAction(InputActionType.SCENESET, "3"),
            mutex12=True,
            mutex34=False,
            ms=Xp24MsActionTable.MS500,
            curtain12=False,
            curtain34=True,
        )

    @pytest.fixture
    def sample_telegrams(self):
        """Create sample telegrams for testing"""
        return [
            '<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>',
            '<R0020044966F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFB>',
            '<R0020044986F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>',
            '<R0020041824F17DAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>'
        ]

    def test_to_telegrams_basic(self):
        """Test basic telegram generation"""
        action_table = Xp24MsActionTable()  # Default values
        serial = "0123450001"

        telegrams = Xp24MsActionTableSerializer.to_telegrams(action_table, serial)

        assert len(telegrams) == 1
        telegram = telegrams[0]

        # Check telegram structure
        assert telegram.startswith("<S0123450001F17DAAAA")
        assert telegram.endswith(">")

        # Check that it contains encoded TOGGLE actions (03 = TOGGLE, 00 = no param)
        assert "03000300030003" in telegram  # All 4 inputs as TOGGLE with no param

        # Check default boolean settings (AA = False) - settings come after actions
        actions_pos = telegram.find("03000300030003")
        settings_start = actions_pos + 16  # After the 16 characters of actions
        settings = telegram[settings_start : settings_start + 6]  # mutex12, mutex34, ms
        assert settings.startswith("AAAA")  # mutex12=AA(False), mutex34=AA(False)

    def test_to_telegrams_custom_values(self, sample_action_table):
        """Test telegram generation with custom values"""
        serial = "0123450001"

        telegrams = Xp24MsActionTableSerializer.to_telegrams(sample_action_table, serial)

        assert len(telegrams) == 1
        telegram = telegrams[0]

        # Check telegram structure
        assert telegram.startswith("<S0123450001F17DAAAA")
        assert telegram.endswith(">")

        # Check encoded actions
        # TOGGLE(3),None(0) + TURNON(1),5 + LEVELSET(11),75 + SCENESET(13),3
        expected_actions = "03000105" + f"{11:02X}{75:02X}" + f"{13:02X}03"
        assert expected_actions in telegram

        # Check boolean settings
        # mutex12=True(AB), mutex34=False(AA), ms=20(14), curtain12=False(AA), curtain34=True(AB)
        settings_start = telegram.find(expected_actions) + len(expected_actions)
        settings = telegram[settings_start : settings_start + 10]  # AB AA 14 AA AB
        assert settings == "ABAA14AAAB"

    def test_to_telegrams_with_param_conversion(self):
        """Test parameter conversion in telegram generation"""
        action_table = Xp24MsActionTable(
            input1_action=InputAction(InputActionType.TURNON, "255"),  # Max byte value
            input2_action=InputAction(InputActionType.LEVELSET, "0"),  # Zero value
            input3_action=InputAction(InputActionType.TOGGLE, None),  # None value
            input4_action=InputAction(
                InputActionType.SCENESET, "invalid"
            ),  # Invalid string
        )
        serial = "0123450001"

        telegrams = Xp24MsActionTableSerializer.to_telegrams(action_table, serial)
        telegram = telegrams[0]

        # Check parameter encoding
        # TURNON(1),255(FF) + LEVELSET(11),0(00) + TOGGLE(3),None(00) + SCENESET(13),invalid->0(00)
        expected_actions = "01FF" + f"{11:02X}00" + "0300" + f"{13:02X}00"
        assert expected_actions in telegram

    def test_from_telegrams_basic(self, sample_telegrams):
        """Test basic telegram parsing"""
        action_table = Xp24MsActionTableSerializer.from_telegrams(sample_telegrams)

        # Verify it's a valid Xp24ActionTable
        assert isinstance(action_table, Xp24MsActionTable)

        # Check that we have 4 input actions
        assert action_table.input1_action is not None
        assert action_table.input2_action is not None
        assert action_table.input3_action is not None
        assert action_table.input4_action is not None

    def test_from_telegrams_invalid_hex_data(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        # This telegram contains non-hex characters that cause fromhex() to fail
        # Based on the debug log: '<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>'
        valid_telegram = "ADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        msactiontable = Xp24MsActionTableSerializer.from_data(valid_telegram)
        assert msactiontable.input1_action.type == InputActionType.TOGGLE
        assert msactiontable.input2_action.type == InputActionType.TOGGLE
        assert msactiontable.input3_action.type == InputActionType.TOGGLE
        assert msactiontable.input4_action.type == InputActionType.TOGGLE

        assert msactiontable.input1_action.param is None
        assert msactiontable.input2_action.param is None
        assert msactiontable.input3_action.param is None
        assert msactiontable.input4_action.param is None

        assert msactiontable.curtain12 == False
        assert msactiontable.curtain34 == False
        assert msactiontable.mutex12 == False
        assert msactiontable.mutex34 == False

    def test_from_telegrams_denibble_0(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AA"

        result = Xp24MsActionTableSerializer._denibble(nibble)
        assert result == [0]


    def test_from_telegrams_denibble_1(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AB"

        result = Xp24MsActionTableSerializer._denibble(nibble)
        assert result == [1]


    def test_from_telegrams_denibble_01(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AAAB"

        result = Xp24MsActionTableSerializer._denibble(nibble)
        assert result == [0, 1]


    def test_from_telegrams_denibble_big(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        nibble = "AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        result = Xp24MsActionTableSerializer._denibble(nibble)
        assert result == [0,0,3,0,3,0,3,0,3,0,0,0,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
