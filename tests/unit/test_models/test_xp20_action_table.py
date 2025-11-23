"""Unit tests for XP20 Action Table models."""

from xp.models.actiontable.msactiontable_xp20 import InputChannel, Xp20MsActionTable


class TestInputChannel:
    """Test cases for InputChannel model."""

    def test_default_values(self):
        """Test that default values are correct."""
        channel = InputChannel()

        assert channel.invert is False
        assert channel.short_long is False
        assert channel.group_on_off is False
        assert len(channel.and_functions) == 8
        assert all(not f for f in channel.and_functions)
        assert channel.sa_function is False
        assert channel.ta_function is False

    def test_custom_values(self):
        """Test setting custom values."""
        and_funcs = [True, False, True, False, True, False, True, False]
        channel = InputChannel(
            invert=True,
            short_long=True,
            group_on_off=True,
            and_functions=and_funcs,
            sa_function=True,
            ta_function=True,
        )

        assert channel.invert is True
        assert channel.short_long is True
        assert channel.group_on_off is True
        assert channel.and_functions == and_funcs
        assert channel.sa_function is True
        assert channel.ta_function is True

    def test_and_functions_initialization(self):
        """Test that and_functions is properly initialized with 8 booleans."""
        channel = InputChannel()
        assert isinstance(channel.and_functions, list)
        assert len(channel.and_functions) == 8
        assert all(isinstance(f, bool) for f in channel.and_functions)

    def test_and_functions_custom_list(self):
        """Test setting custom and_functions list."""
        custom_funcs = [True, True, False, False, True, True, False, False]
        channel = InputChannel(and_functions=custom_funcs)
        assert channel.and_functions == custom_funcs

    def test_boolean_types(self):
        """Test that all fields are properly typed as booleans."""
        channel = InputChannel(
            invert=True,
            short_long=False,
            group_on_off=True,
            sa_function=False,
            ta_function=True,
        )

        assert isinstance(channel.invert, bool)
        assert isinstance(channel.short_long, bool)
        assert isinstance(channel.group_on_off, bool)
        assert isinstance(channel.sa_function, bool)
        assert isinstance(channel.ta_function, bool)


class TestXp20MsActionTable:
    """Test cases for Xp20MsActionTable model."""

    def test_default_values(self):
        """Test that default values are correct."""
        table = Xp20MsActionTable()

        # Check all 8 input channels exist
        for i in range(1, 9):
            channel = getattr(table, f"input{i}")
            assert isinstance(channel, InputChannel)
            assert channel.invert is False
            assert channel.short_long is False
            assert channel.group_on_off is False
            assert len(channel.and_functions) == 8
            assert all(not f for f in channel.and_functions)
            assert channel.sa_function is False
            assert channel.ta_function is False

    def test_custom_input_channels(self):
        """Test setting custom input channels."""
        channel1 = InputChannel(invert=True, short_long=True)
        channel2 = InputChannel(group_on_off=True, sa_function=True)

        table = Xp20MsActionTable(input1=channel1, input2=channel2)

        assert table.input1.invert is True
        assert table.input1.short_long is True
        assert table.input2.group_on_off is True
        assert table.input2.sa_function is True

    def test_all_inputs_exist(self):
        """Test that all 8 input channels are present."""
        table = Xp20MsActionTable()

        assert hasattr(table, "input1")
        assert hasattr(table, "input2")
        assert hasattr(table, "input3")
        assert hasattr(table, "input4")
        assert hasattr(table, "input5")
        assert hasattr(table, "input6")
        assert hasattr(table, "input7")
        assert hasattr(table, "input8")

        # Verify they're all InputChannel instances
        for i in range(1, 9):
            channel = getattr(table, f"input{i}")
            assert isinstance(channel, InputChannel)

    def test_complex_configuration(self):
        """Test a complex configuration with mixed settings."""
        table = Xp20MsActionTable()

        # Configure input1 with all flags true
        table.input1.invert = True
        table.input1.short_long = True
        table.input1.group_on_off = True
        table.input1.and_functions = [True] * 8
        table.input1.sa_function = True
        table.input1.ta_function = True

        # Configure input2 with mixed flags
        table.input2.invert = False
        table.input2.short_long = True
        table.input2.group_on_off = False
        table.input2.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]
        table.input2.sa_function = True
        table.input2.ta_function = False

        # Verify configurations
        assert table.input1.invert is True
        assert table.input1.short_long is True
        assert table.input1.group_on_off is True
        assert table.input1.and_functions == [True] * 8
        assert table.input1.sa_function is True
        assert table.input1.ta_function is True

        assert table.input2.invert is False
        assert table.input2.short_long is True
        assert table.input2.group_on_off is False
        assert table.input2.and_functions == [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]
        assert table.input2.sa_function is True
        assert table.input2.ta_function is False

        # Other inputs should still have defaults
        assert table.input3.invert is False
        assert table.input8.sa_function is False

    def test_dataclass_equality(self):
        """Test that dataclass equality works correctly."""
        table1 = Xp20MsActionTable()
        table2 = Xp20MsActionTable()

        # Default instances should be equal
        assert table1 == table2

        # Modify one and they should be different
        table1.input1.invert = True
        assert table1 != table2

        # Modify the other to match and they should be equal again
        table2.input1.invert = True
        assert table1 == table2

    def test_input_channel_independence(self):
        """Test that input channels are independent of each other."""
        table = Xp20MsActionTable()

        # Modify input1
        table.input1.invert = True
        table.input1.and_functions[0] = True

        # Other inputs should remain unchanged
        assert table.input2.invert is False
        assert table.input2.and_functions[0] is False
        assert table.input8.invert is False

        # Modify input2
        table.input2.short_long = True

        # input1 should remain as modified, others unchanged
        assert table.input1.invert is True
        assert table.input1.short_long is False  # Still default
        assert table.input2.short_long is True
        assert table.input3.short_long is False

    def test_and_functions_list_independence(self):
        """Test that and_functions lists are independent between channels."""
        table = Xp20MsActionTable()

        # Modify input1's and_functions
        table.input1.and_functions[0] = True
        table.input1.and_functions[7] = True

        # Other inputs should have their own lists
        assert table.input2.and_functions[0] is False
        assert table.input2.and_functions[7] is False

        # Verify input1 changes are preserved
        assert table.input1.and_functions[0] is True
        assert table.input1.and_functions[7] is True
        assert table.input1.and_functions[1] is False  # Unchanged


class TestXp20ShortFormat:
    """Test cases for XP20 short format serialization."""

    def test_to_short_format_default(self):
        """Test short format with default (all zeros) configuration."""
        lines = Xp20MsActionTable().to_short_format()

        assert len(lines) == 8
        for i, line in enumerate(lines, 1):
            assert line == f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0"

    def test_to_short_format_single_channel(self):
        """Test short format with single channel configured."""
        table = Xp20MsActionTable()
        table.input1.invert = True
        table.input1.short_long = True
        table.input1.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]

        lines = table.to_short_format()

        assert lines[0] == "CH1 I:1 S:1 G:0 AND:10101010 SA:0 TA:0"
        assert lines[1] == "CH2 I:0 S:0 G:0 AND:00000000 SA:0 TA:0"

    def test_to_short_format_all_flags_enabled(self):
        """Test short format with all flags enabled."""
        table = Xp20MsActionTable()
        table.input1.invert = True
        table.input1.short_long = True
        table.input1.group_on_off = True
        table.input1.and_functions = [True] * 8
        table.input1.sa_function = True
        table.input1.ta_function = True

        lines = table.to_short_format()

        assert lines[0] == "CH1 I:1 S:1 G:1 AND:11111111 SA:1 TA:1"

    def test_to_short_format_mixed_configuration(self):
        """Test short format with mixed configuration across channels."""
        table = Xp20MsActionTable()
        table.input1.invert = True
        table.input1.group_on_off = True
        table.input1.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]
        table.input1.ta_function = True

        table.input2.short_long = True
        table.input2.and_functions = [
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
        ]
        table.input2.sa_function = True

        table.input3.invert = True
        table.input3.short_long = True
        table.input3.group_on_off = True
        table.input3.and_functions = [
            True,
            True,
            False,
            False,
            True,
            True,
            False,
            False,
        ]
        table.input3.sa_function = True
        table.input3.ta_function = True

        lines = table.to_short_format()

        assert lines[0] == "CH1 I:1 S:0 G:1 AND:10101010 SA:0 TA:1"
        assert lines[1] == "CH2 I:0 S:1 G:0 AND:01010101 SA:1 TA:0"
        assert lines[2] == "CH3 I:1 S:1 G:1 AND:11001100 SA:1 TA:1"
        assert lines[3] == "CH4 I:0 S:0 G:0 AND:00000000 SA:0 TA:0"

    def test_from_short_format_default(self):
        """Test parsing short format with default configuration."""
        short = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 9)]

        table = Xp20MsActionTable.from_short_format(short)

        for i in range(1, 9):
            channel = getattr(table, f"input{i}")
            assert channel.invert is False
            assert channel.short_long is False
            assert channel.group_on_off is False
            assert channel.and_functions == [False] * 8
            assert channel.sa_function is False
            assert channel.ta_function is False

    def test_from_short_format_single_channel(self):
        """Test parsing short format with single channel configured."""
        lines = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 9)]
        lines[0] = "CH1 I:1 S:1 G:0 AND:10101010 SA:0 TA:0"

        table = Xp20MsActionTable.from_short_format(lines)

        assert table.input1.invert is True
        assert table.input1.short_long is True
        assert table.input1.and_functions == [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]
        assert table.input2.invert is False

    def test_from_short_format_all_flags_enabled(self):
        """Test parsing short format with all flags enabled."""
        lines = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 9)]
        lines[0] = "CH1 I:1 S:1 G:1 AND:11111111 SA:1 TA:1"

        table = Xp20MsActionTable.from_short_format(lines)

        assert table.input1.invert is True
        assert table.input1.short_long is True
        assert table.input1.group_on_off is True
        assert table.input1.and_functions == [True] * 8
        assert table.input1.sa_function is True
        assert table.input1.ta_function is True

    def test_from_short_format_mixed_configuration(self):
        """Test parsing short format with mixed configuration."""
        short = [
            "CH1 I:1 S:0 G:1 AND:10101010 SA:0 TA:1",
            "CH2 I:0 S:1 G:0 AND:01010101 SA:1 TA:0",
            "CH3 I:1 S:1 G:1 AND:11001100 SA:1 TA:1",
            "CH4 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "CH5 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "CH6 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "CH7 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "CH8 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
        ]

        table = Xp20MsActionTable.from_short_format(short)

        assert table.input1.invert is True
        assert table.input1.group_on_off is True
        assert table.input1.ta_function is True
        assert table.input2.short_long is True
        assert table.input2.sa_function is True
        assert table.input3.invert is True
        assert table.input3.short_long is True
        assert table.input3.group_on_off is True

    def test_round_trip_conversion_default(self):
        """Test round-trip conversion with default configuration."""
        table1 = Xp20MsActionTable()
        short = table1.to_short_format()
        table2 = Xp20MsActionTable.from_short_format(short)
        assert table1 == table2

    def test_round_trip_conversion_complex(self):
        """Test round-trip conversion with complex configuration."""
        table1 = Xp20MsActionTable()
        table1.input1.invert = True
        table1.input1.short_long = True
        table1.input1.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]
        table1.input2.group_on_off = True
        table1.input2.sa_function = True
        table1.input3.ta_function = True
        table1.input3.and_functions = [
            False,
            False,
            True,
            True,
            False,
            False,
            True,
            True,
        ]
        table1.input8.invert = True
        table1.input8.and_functions = [True] * 8

        short = table1.to_short_format()
        table2 = Xp20MsActionTable.from_short_format(short)

        assert table1 == table2

    def test_from_short_format_invalid_line_count(self):
        """Test parsing fails with wrong number of lines."""
        short = ["CH1 I:0 S:0 G:0 AND:00000000 SA:0 TA:0"] * 5

        try:
            Xp20MsActionTable.from_short_format(short)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Expected 8 channel lines" in str(e)

    def test_from_short_format_invalid_format(self):
        """Test parsing fails with invalid format."""
        lines = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 9)]
        lines[0] = "INVALID FORMAT"

        try:
            Xp20MsActionTable.from_short_format(lines)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid channel format" in str(e)

    def test_from_short_format_invalid_channel_number(self):
        """Test parsing fails with invalid channel number."""
        lines = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 9)]
        lines[0] = "CH9 I:0 S:0 G:0 AND:00000000 SA:0 TA:0"

        try:
            Xp20MsActionTable.from_short_format(lines)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid channel format" in str(e)

    def test_from_short_format_invalid_binary_value(self):
        """Test parsing fails with invalid binary value in AND field."""
        lines = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 9)]
        lines[0] = "CH1 I:0 S:0 G:0 AND:00000002 SA:0 TA:0"

        try:
            Xp20MsActionTable.from_short_format(lines)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid channel format" in str(e)

    def test_from_short_format_missing_channel(self):
        """Test parsing fails when a channel is missing."""
        lines = [f"CH{i} I:0 S:0 G:0 AND:00000000 SA:0 TA:0" for i in range(1, 8)]

        try:
            Xp20MsActionTable.from_short_format(lines)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Expected 8 channel lines" in str(e)

    def test_from_short_format_with_whitespace(self):
        """Test parsing handles leading/trailing whitespace."""
        short = [
            "  CH1 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH2 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH3 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH4 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH5 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH6 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH7 I:0 S:0 G:0 AND:00000000 SA:0 TA:0",
            "  CH8 I:0 S:0 G:0 AND:00000000 SA:0 TA:0  ",
        ]

        table = Xp20MsActionTable.from_short_format(short)
        assert table is not None
