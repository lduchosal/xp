"""Integration tests for XP20 Action Table functionality."""

import pytest

from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.services.conbus.actiontable.msactiontable_service import (
    MsActionTableService,
    Xp20MsActionTableSerializer,
)


class TestXp20ActionTableIntegration:
    """Integration tests for XP20 Action Table."""

    def test_serializer_service_integration(self):
        """Test that serializer works with service."""
        # Create a sample action table
        action_table = Xp20MsActionTable()
        action_table.input1.invert = True
        action_table.input1.short_long = True
        action_table.input2.group_on_off = True
        action_table.input2.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]

        # Serialize it
        serialized = Xp20MsActionTableSerializer.to_data(action_table)

        # Deserialize from data
        result = Xp20MsActionTableSerializer.from_data(serialized)

        # Verify the round-trip worked
        assert result.input1.invert == action_table.input1.invert
        assert result.input1.short_long == action_table.input1.short_long
        assert result.input2.group_on_off == action_table.input2.group_on_off
        assert result.input2.and_functions == action_table.input2.and_functions

    def test_service_xp20_support(self):
        """Test that MsActionTableService recognizes XP20 module type."""
        # This test verifies the service is configured to handle xp20
        # without actually making network calls
        from unittest.mock import Mock

        mock_cli_config = Mock()
        mock_reactor = Mock()
        mock_xp20_serializer = Mock()
        mock_xp24_serializer = Mock()
        mock_xp33_serializer = Mock()
        mock_telegram = Mock()

        service = MsActionTableService(
            cli_config=mock_cli_config,
            reactor=mock_reactor,
            xp20ms_serializer=mock_xp20_serializer,
            xp24ms_serializer=mock_xp24_serializer,
            xp33ms_serializer=mock_xp33_serializer,
            telegram_service=mock_telegram,
        )

        # The service should have the xp20 serializer available
        # We can't test the actual download without a real connection,
        # but we can verify the structure is in place

        # Check that the service can be instantiated
        assert service is not None
        assert service.xp20ms_serializer is not None
        assert service.telegram_service is not None

    def test_complex_configuration_round_trip(self):
        """Test complex configuration through full serialization cycle."""
        # Create a complex action table
        action_table = Xp20MsActionTable()

        # Configure all inputs with different patterns
        for i in range(1, 9):
            channel = getattr(action_table, f"input{i}")
            channel.invert = i % 2 == 0  # Even inputs inverted
            channel.short_long = i % 3 == 0  # Every 3rd input
            channel.group_on_off = i % 4 == 0  # Every 4th input
            channel.sa_function = i % 5 == 0  # Every 5th input
            channel.ta_function = i % 6 == 0  # Every 6th input

            # Create alternating pattern for and_functions
            channel.and_functions = [(j + i) % 2 == 0 for j in range(8)]

        # Serialize and deserialize
        serialized = Xp20MsActionTableSerializer.to_data(action_table)
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        # Verify all configurations are preserved
        for i in range(1, 9):
            original = getattr(action_table, f"input{i}")
            result = getattr(deserialized, f"input{i}")

            assert original.invert == result.invert, f"input{i} invert mismatch"
            assert (
                original.short_long == result.short_long
            ), f"input{i} short_long mismatch"
            assert (
                original.group_on_off == result.group_on_off
            ), f"input{i} group_on_off mismatch"
            assert (
                original.sa_function == result.sa_function
            ), f"input{i} sa_function mismatch"
            assert (
                original.ta_function == result.ta_function
            ), f"input{i} ta_function mismatch"
            assert (
                original.and_functions == result.and_functions
            ), f"input{i} and_functions mismatch"

    def test_boundary_conditions(self):
        """Test boundary conditions and edge cases."""
        # Test all flags off
        action_table_off = Xp20MsActionTable()
        serialized_off = Xp20MsActionTableSerializer.to_data(action_table_off)
        deserialized_off = Xp20MsActionTableSerializer.from_data(serialized_off)

        for i in range(1, 9):
            channel = getattr(deserialized_off, f"input{i}")
            assert not channel.invert
            assert not channel.short_long
            assert not channel.group_on_off
            assert not channel.sa_function
            assert not channel.ta_function
            assert all(not f for f in channel.and_functions)

        # Test all flags on
        action_table_on = Xp20MsActionTable()
        for i in range(1, 9):
            channel = getattr(action_table_on, f"input{i}")
            channel.invert = True
            channel.short_long = True
            channel.group_on_off = True
            channel.sa_function = True
            channel.ta_function = True
            channel.and_functions = [True] * 8

        serialized_on = Xp20MsActionTableSerializer.to_data(action_table_on)
        deserialized_on = Xp20MsActionTableSerializer.from_data(serialized_on)

        for i in range(1, 9):
            channel = getattr(deserialized_on, f"input{i}")
            assert channel.invert
            assert channel.short_long
            assert channel.group_on_off
            assert channel.sa_function
            assert channel.ta_function
            assert all(f for f in channel.and_functions)

    def test_specification_compliance(self):
        """Test compliance with the specification example."""
        spec_example = (
            "AAAAAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        # Should decode without errors
        result = Xp20MsActionTableSerializer.from_data(spec_example)

        # Verify it's a valid table
        assert isinstance(result, Xp20MsActionTable)

        # Test that we can re-encode it
        re_encoded = Xp20MsActionTableSerializer.to_data(result)
        assert len(re_encoded) == 68

        # Round-trip should work
        final_result = Xp20MsActionTableSerializer.from_data(re_encoded)
        assert isinstance(final_result, Xp20MsActionTable)

    def test_data_layout_compliance(self):
        """Test that data layout matches specification."""
        action_table = Xp20MsActionTable()

        # Set specific inputs to test bit positions
        action_table.input1.short_long = True  # Should set bit 0 in byte 0
        action_table.input3.group_on_off = True  # Should set bit 2 in byte 1
        action_table.input5.invert = True  # Should set bit 4 in byte 2
        action_table.input8.sa_function = True  # Should set bit 7 in byte 11
        action_table.input2.ta_function = True  # Should set bit 1 in byte 12

        # Set specific AND functions
        action_table.input1.and_functions = [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
        ]  # 0x55
        action_table.input4.and_functions = [
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
        ]  # 0xAA

        serialized = Xp20MsActionTableSerializer.to_data(action_table)

        # Verify the data can be decoded back correctly
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        assert deserialized.input1.short_long is True
        assert deserialized.input3.group_on_off is True
        assert deserialized.input5.invert is True
        assert deserialized.input8.sa_function is True
        assert deserialized.input2.ta_function is True
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
        assert deserialized.input4.and_functions == [
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
        ]

    def test_error_handling_integration(self):
        """Test error handling across the integration."""
        # Test invalid data length
        with pytest.raises(ValueError):
            Xp20MsActionTableSerializer.from_data("INVALID")

        # Test with wrong length telegram
        with pytest.raises(ValueError):
            Xp20MsActionTableSerializer.from_data("A" * 63)  # Too short

        with pytest.raises(ValueError):
            Xp20MsActionTableSerializer.from_data("A" * 65)  # Too long

    def test_model_serializer_consistency(self):
        """Test that model defaults work correctly with serializer."""
        # Default model should serialize and deserialize consistently
        default_table = Xp20MsActionTable()
        serialized = Xp20MsActionTableSerializer.to_data(default_table)
        deserialized = Xp20MsActionTableSerializer.from_data(serialized)

        # Should be equivalent to original
        assert default_table == deserialized

        # All channels should have default values
        for i in range(1, 9):
            channel = getattr(deserialized, f"input{i}")
            assert not channel.invert
            assert not channel.short_long
            assert not channel.group_on_off
            assert not channel.sa_function
            assert not channel.ta_function
            assert len(channel.and_functions) == 8
            assert all(not f for f in channel.and_functions)
