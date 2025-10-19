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
