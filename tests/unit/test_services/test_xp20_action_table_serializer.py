"""Unit tests for XP20 Action Table Serializer."""

import pytest

from xp.models.actiontable.msactiontable_xp20 import InputChannel, Xp20MsActionTable
from xp.services.actiontable.msactiontable_xp20_serializer import (
    GROUP_ON_OFF_INDEX,
    INVERT_INDEX,
    SA_FUNCTION_INDEX,
    SHORT_LONG_INDEX,
    TA_FUNCTION_INDEX,
    Xp20MsActionTableSerializer,
)
from xp.utils.serialization import de_nibbles


class TestXp20MsActionTableSerializer:
    """Test cases for Xp20MsActionTableSerializer."""

    @pytest.fixture
    def sample_action_table(self):
        """Create sample action table for testing."""
        return Xp20MsActionTable(
            input1=InputChannel(
                invert=True,
                short_long=False,
                group_on_off=True,
                and_functions=[True, False, True, False, True, False, True, False],
                sa_function=False,
                ta_function=True,
            ),
            input2=InputChannel(
                invert=False,
                short_long=True,
                group_on_off=False,
                and_functions=[False, True, False, True, False, True, False, True],
                sa_function=True,
                ta_function=False,
            ),
            input3=InputChannel(
                invert=True,
                short_long=True,
                group_on_off=True,
                and_functions=[True, True, False, False, True, True, False, False],
                sa_function=True,
                ta_function=True,
            ),
            input4=InputChannel(),  # Default values
            input5=InputChannel(),
            input6=InputChannel(),
            input7=InputChannel(),
            input8=InputChannel(),
        )

    @pytest.fixture
    def sample_telegram_data(self):
        """Sample telegram data based on specification example (68 chars)."""
        return "AAAAAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

    def test_to_data_serialization(self, sample_action_table):
        """Test serialization to telegram format."""
        result = Xp20MsActionTableSerializer.to_data(sample_action_table)

        # Should return 64-character hex string
        assert len(result) == 68
        assert all(c in "ABCDEFGHIJKLMNOP" for c in result)

    def test_from_data_deserialization(self, sample_telegram_data):
        """Test deserialization from telegram data."""
        action_table = Xp20MsActionTableSerializer.from_data(sample_telegram_data)

        # Verify it's a valid Xp20MsActionTable
        assert isinstance(action_table, Xp20MsActionTable)

        # Check that we have 8 input channels
        assert action_table.input1 is not None
        assert action_table.input2 is not None
        assert action_table.input3 is not None
        assert action_table.input4 is not None
        assert action_table.input5 is not None
        assert action_table.input6 is not None
        assert action_table.input7 is not None
        assert action_table.input8 is not None

    def test_round_trip_serialization(self, sample_action_table):
        """Test that serialization followed by deserialization preserves data."""
        # Serialize to data
        serialized = Xp20MsActionTableSerializer.to_data(sample_action_table)

        # Deserialize back
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        # Verify all input channels match
        assert deserialized.input1.invert == sample_action_table.input1.invert
        assert deserialized.input1.short_long == sample_action_table.input1.short_long
        assert (
            deserialized.input1.group_on_off == sample_action_table.input1.group_on_off
        )
        assert (
            deserialized.input1.and_functions
            == sample_action_table.input1.and_functions
        )
        assert deserialized.input1.sa_function == sample_action_table.input1.sa_function
        assert deserialized.input1.ta_function == sample_action_table.input1.ta_function

        assert deserialized.input2.invert == sample_action_table.input2.invert
        assert deserialized.input2.short_long == sample_action_table.input2.short_long
        assert (
            deserialized.input2.group_on_off == sample_action_table.input2.group_on_off
        )
        assert (
            deserialized.input2.and_functions
            == sample_action_table.input2.and_functions
        )
        assert deserialized.input2.sa_function == sample_action_table.input2.sa_function
        assert deserialized.input2.ta_function == sample_action_table.input2.ta_function

    def test_invalid_data_length(self):
        """Test that invalid data length raises ValueError."""
        with pytest.raises(ValueError, match="must be 68 characters long"):
            Xp20MsActionTableSerializer.from_data("INVALID")

    def test_byte_to_bits_conversion(self):
        """Test byte to bits conversion helper."""
        from xp.utils.serialization import byte_to_bits

        # Test known values
        assert byte_to_bits(0) == [False] * 8
        assert byte_to_bits(255) == [True] * 8
        assert byte_to_bits(1) == [True] + [False] * 7
        assert byte_to_bits(128) == [False] * 7 + [True]
        assert byte_to_bits(85) == [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]

    def test_default_input_channel(self):
        """Test that default input channel has correct values."""
        channel = InputChannel()
        assert channel.invert is False
        assert channel.short_long is False
        assert channel.group_on_off is False
        assert len(channel.and_functions) == 8
        assert all(not f for f in channel.and_functions)
        assert channel.sa_function is False
        assert channel.ta_function is False

    def test_and_functions_encoding(self):
        """Test AND functions encoding/decoding."""
        action_table = Xp20MsActionTable()
        action_table.input1.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]

        serialized = Xp20MsActionTableSerializer.to_data(action_table)
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        assert deserialized.input1.and_functions == [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]

    def test_all_flags_true(self):
        """Test encoding/decoding with all flags set to True."""
        action_table = Xp20MsActionTable()
        for i in range(1, 9):
            channel = getattr(action_table, f"input{i}")
            channel.invert = True
            channel.short_long = True
            channel.group_on_off = True
            channel.and_functions = [True] * 8
            channel.sa_function = True
            channel.ta_function = True

        serialized = Xp20MsActionTableSerializer.to_data(action_table)
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        # Verify all flags are preserved
        for i in range(1, 9):
            channel = getattr(deserialized, f"input{i}")
            assert channel.invert is True
            assert channel.short_long is True
            assert channel.group_on_off is True
            assert channel.and_functions == [True] * 8
            assert channel.sa_function is True
            assert channel.ta_function is True

    def test_encoding_bit_positions(self):
        """Test that bit positions are correctly encoded."""
        action_table = Xp20MsActionTable()

        # Set specific bits for input1 (position 0)
        action_table.input1.invert = True
        action_table.input1.short_long = True
        action_table.input1.sa_function = True

        # Set specific bits for input8 (position 7)
        action_table.input8.group_on_off = True
        action_table.input8.ta_function = True

        serialized = Xp20MsActionTableSerializer.to_data(action_table)
        # Skip the 4-character "AAAA" prefix when de-nibbling
        raw_bytes = de_nibbles(serialized[4:])

        # Check bit positions
        assert raw_bytes[SHORT_LONG_INDEX] & 1 != 0  # input1 bit 0
        assert raw_bytes[INVERT_INDEX] & 1 != 0  # input1 bit 0
        assert raw_bytes[SA_FUNCTION_INDEX] & 1 != 0  # input1 bit 0
        assert raw_bytes[GROUP_ON_OFF_INDEX] & 128 != 0  # input8 bit 7
        assert raw_bytes[TA_FUNCTION_INDEX] & 128 != 0  # input8 bit 7

    def test_specification_example(self):
        """Test with the example telegram from specification."""
        example_data = (
            "AAAAAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        # This should decode without errors
        result = Xp20MsActionTableSerializer.from_data(example_data)
        assert isinstance(result, Xp20MsActionTable)

        # Test round-trip
        re_encoded = Xp20MsActionTableSerializer.to_data(result)
        re_decoded = Xp20MsActionTableSerializer.from_data(re_encoded)

        # Should be identical
        for i in range(1, 9):
            original_channel = getattr(result, f"input{i}")
            decoded_channel = getattr(re_decoded, f"input{i}")

            assert original_channel.invert == decoded_channel.invert
            assert original_channel.short_long == decoded_channel.short_long
            assert original_channel.group_on_off == decoded_channel.group_on_off
            assert original_channel.and_functions == decoded_channel.and_functions
            assert original_channel.sa_function == decoded_channel.sa_function
            assert original_channel.ta_function == decoded_channel.ta_function

    def test_from_telegrams_from_data(self):
        """Test round-trip serialization with default/empty action table data."""
        # 64 characters - all A's represent a completely empty/default action table
        valid_msactiontable = (
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        # Deserialize from data
        msactiontable = Xp20MsActionTableSerializer.from_data(valid_msactiontable)

        # Verify it's a valid Xp20MsActionTable with default values
        assert isinstance(msactiontable, Xp20MsActionTable)
        for i in range(1, 9):
            channel = getattr(msactiontable, f"input{i}")
            assert channel.invert is False
            assert channel.short_long is False
            assert channel.group_on_off is False
            assert channel.and_functions == [False] * 8
            assert channel.sa_function is False
            assert channel.ta_function is False

        # Re-serialize back to data
        msactiontable_data = Xp20MsActionTableSerializer.to_data(msactiontable)

        # Verify round-trip preserves the original data
        assert valid_msactiontable == msactiontable_data

    def test_real_xp20_telegram(self):
        """Test deserialization of a real XP20 msactiontable telegram."""
        # Real telegram from XP20 device
        telegram = "<R0020041824F17DAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>"

        # Extract data portion (skip header at 0-15, skip count at 16-19, take 64 chars at 20-83)
        data = telegram[16:84]
        assert len(data) == 68

        # Deserialize the action table
        action_table = Xp20MsActionTableSerializer.from_data(data)

        # Verify it's a valid Xp20MsActionTable
        assert isinstance(action_table, Xp20MsActionTable)

        # Verify all 8 input channels are present
        for i in range(1, 9):
            channel = getattr(action_table, f"input{i}")
            assert channel is not None
            assert isinstance(channel, InputChannel)

        # Test round-trip: serialize and deserialize should preserve data
        serialized = Xp20MsActionTableSerializer.to_data(action_table)
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        # Verify round-trip preserves all values
        for i in range(1, 9):
            original = getattr(action_table, f"input{i}")
            result = getattr(deserialized, f"input{i}")

            assert original.invert == result.invert
            assert original.short_long == result.short_long
            assert original.group_on_off == result.group_on_off
            assert original.and_functions == result.and_functions
            assert original.sa_function == result.sa_function
            assert original.ta_function == result.ta_function

    def test_serialize_back_and_forth(self):
        """Test that default values work correctly."""
        telegram = "<R0020037487F17DAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFL>"

        # Test serialization with defaults
        serialized_table = telegram[16:84]
        deserialized = Xp20MsActionTableSerializer.from_data(serialized_table)
        serialized = Xp20MsActionTableSerializer.to_data(deserialized)

        assert serialized_table == serialized
