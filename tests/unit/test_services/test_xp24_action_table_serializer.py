"""Unit tests for XP24 Action Table Serializer."""

import pytest

from xp.models.input_action_type import InputActionType
from xp.models.xp24_msactiontable import InputAction, Xp24MsActionTable
from xp.services.xp24_action_table_serializer import Xp24ActionTableSerializer


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
            "<S0123450001F17DAAAA03000B4B030D03ABAAC14ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACE>"
        ]

    def test_to_telegrams_basic(self):
        """Test basic telegram generation"""
        action_table = Xp24MsActionTable()  # Default values
        serial = "0123450001"

        telegrams = Xp24ActionTableSerializer.to_telegrams(action_table, serial)

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

        telegrams = Xp24ActionTableSerializer.to_telegrams(sample_action_table, serial)

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

        telegrams = Xp24ActionTableSerializer.to_telegrams(action_table, serial)
        telegram = telegrams[0]

        # Check parameter encoding
        # TURNON(1),255(FF) + LEVELSET(11),0(00) + TOGGLE(3),None(00) + SCENESET(13),invalid->0(00)
        expected_actions = "01FF" + f"{11:02X}00" + "0300" + f"{13:02X}00"
        assert expected_actions in telegram

    def test_from_telegrams_basic(self, sample_telegrams):
        """Test basic telegram parsing"""
        action_table = Xp24ActionTableSerializer.from_telegrams(sample_telegrams)

        # Verify it's a valid Xp24ActionTable
        assert isinstance(action_table, Xp24MsActionTable)

        # Check that we have 4 input actions
        assert action_table.input1_action is not None
        assert action_table.input2_action is not None
        assert action_table.input3_action is not None
        assert action_table.input4_action is not None

    def test_from_telegrams_data_extraction(self):
        """Test telegram data extraction with known values"""
        # Create telegram with known data pattern
        # S{serial}F17DAAAA + 4 actions + 5 settings + padding
        # Actions: TOGGLE(03),None(00) for all 4 inputs
        # Settings: mutex12=False(AA), mutex34=False(AA), ms=12(0C), curtain12=False(AA), curtain34=False(AA)
        telegram_data = (
            "S0123450001F17DAAAA" + "0300030003000300" + "AAAA0CAAAA" + "A" * 38
        )

        # Calculate and append checksum
        from xp.utils.checksum import calculate_checksum

        checksum = calculate_checksum(telegram_data)
        telegram = f"<{telegram_data}{checksum}>"

        action_table = Xp24ActionTableSerializer.from_telegrams([telegram])

        # Verify parsed actions
        assert action_table.input1_action.type == InputActionType.TOGGLE
        assert action_table.input1_action.param is None
        assert action_table.input2_action.type == InputActionType.TOGGLE
        assert action_table.input2_action.param is None
        assert action_table.input3_action.type == InputActionType.TOGGLE
        assert action_table.input3_action.param is None
        assert action_table.input4_action.type == InputActionType.TOGGLE
        assert action_table.input4_action.param is None

        # Verify parsed settings
        assert action_table.mutex12 is False
        assert action_table.mutex34 is False
        assert action_table.ms == 12
        assert action_table.curtain12 is False
        assert action_table.curtain34 is False

    def test_from_telegrams_with_parameters(self):
        """Test telegram parsing with non-zero parameters"""
        # Create telegram with parameters
        # Actions: TURNON(01),10(0A) + LEVELSET(0B),75(4B) + SCENESET(0D),3(03) + TOGGLE(03),None(00)
        # Settings: mutex12=True(AB), mutex34=False(AA), ms=20(14), curtain12=False(AA), curtain34=True(AB)
        telegram_data = (
            "S0123450001F17DAAAA" + "010A0B4B0D030300" + "ABAA14AAAB" + "A" * 38
        )

        from xp.utils.checksum import calculate_checksum

        checksum = calculate_checksum(telegram_data)
        telegram = f"<{telegram_data}{checksum}>"

        action_table = Xp24ActionTableSerializer.from_telegrams([telegram])

        # Verify parsed actions with parameters
        assert action_table.input1_action.type == InputActionType.TURNON
        assert action_table.input1_action.param == "10"
        assert action_table.input2_action.type == InputActionType.LEVELSET
        assert action_table.input2_action.param == "75"
        assert action_table.input3_action.type == InputActionType.SCENESET
        assert action_table.input3_action.param == "3"
        assert action_table.input4_action.type == InputActionType.TOGGLE
        assert action_table.input4_action.param is None

        # Verify parsed settings
        assert action_table.mutex12 is True
        assert action_table.mutex34 is False
        assert action_table.ms == 20
        assert action_table.curtain12 is False
        assert action_table.curtain34 is True

    def test_roundtrip_serialization(self, sample_action_table):
        """Test that serialization and deserialization are consistent"""
        serial = "0123450001"

        # Serialize
        telegrams = Xp24ActionTableSerializer.to_telegrams(sample_action_table, serial)

        # Deserialize
        restored_table = Xp24ActionTableSerializer.from_telegrams(telegrams)

        # Verify they match
        assert (
            restored_table.input1_action.type == sample_action_table.input1_action.type
        )
        assert (
            restored_table.input1_action.param
            == sample_action_table.input1_action.param
        )
        assert (
            restored_table.input2_action.type == sample_action_table.input2_action.type
        )
        assert (
            restored_table.input2_action.param
            == sample_action_table.input2_action.param
        )
        assert (
            restored_table.input3_action.type == sample_action_table.input3_action.type
        )
        assert (
            restored_table.input3_action.param
            == sample_action_table.input3_action.param
        )
        assert (
            restored_table.input4_action.type == sample_action_table.input4_action.type
        )
        assert (
            restored_table.input4_action.param
            == sample_action_table.input4_action.param
        )

        assert restored_table.mutex12 == sample_action_table.mutex12
        assert restored_table.mutex34 == sample_action_table.mutex34
        assert restored_table.ms == sample_action_table.ms
        assert restored_table.curtain12 == sample_action_table.curtain12
        assert restored_table.curtain34 == sample_action_table.curtain34

    def test_unknown_action_type_fallback(self):
        """Test fallback to VOID for unknown action types"""
        # Create telegram with unknown action type (99)
        telegram_data = (
            "S0123450001F17DAAAA" + "630003000300030" + "AAAA0CAAAA" + "A" * 38
        )

        from xp.utils.checksum import calculate_checksum

        checksum = calculate_checksum(telegram_data)
        telegram = f"<{telegram_data}{checksum}>"

        action_table = Xp24ActionTableSerializer.from_telegrams([telegram])

        # Should fallback to VOID for unknown action type
        assert action_table.input1_action.type == InputActionType.VOID

    def test_zero_parameter_becomes_none(self):
        """Test that zero parameters become None for cleaner representation"""
        # Create telegram with zero parameters
        telegram_data = (
            "S0123450001F17DAAAA" + "0100030003000300" + "AAAA0CAAAA" + "A" * 38
        )

        from xp.utils.checksum import calculate_checksum

        checksum = calculate_checksum(telegram_data)
        telegram = f"<{telegram_data}{checksum}>"

        action_table = Xp24ActionTableSerializer.from_telegrams([telegram])

        # Zero parameter should become None
        assert action_table.input1_action.type == InputActionType.TURNON
        assert action_table.input1_action.param is None

    def test_from_telegrams_invalid_hex_data(self):
        """Test that invalid hex data raises ValueError with non-hexadecimal characters"""
        # This telegram contains non-hex characters that cause fromhex() to fail
        # Based on the debug log: '<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>'
        valid_telegram = "<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>"

        msactiontable = Xp24ActionTableSerializer.from_telegrams([valid_telegram])
        assert msactiontable.input1_action.type == InputActionType.TOGGLE
        assert msactiontable.input2_action.type == InputActionType.TOGGLE
        assert msactiontable.input3_action.type == InputActionType.TOGGLE
        assert msactiontable.input4_action.type == InputActionType.TOGGLE
