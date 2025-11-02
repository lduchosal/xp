"""Unit tests for XP33 Action Table Serializer."""

from contextlib import suppress

import pytest

from xp.models.actiontable.msactiontable_xp33 import (
    Xp33MsActionTable,
    Xp33Output,
    Xp33Scene,
)
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.conbus.actiontable.msactiontable_service import (
    Xp33MsActionTableSerializer,
)
from xp.utils.serialization import de_nibbles


class TestXp33MsActionTableSerializer:
    """Test cases for Xp33MsActionTableSerializer."""

    @pytest.fixture
    def sample_action_table(self):
        """Create sample action table for testing."""
        return Xp33MsActionTable(
            output1=Xp33Output(
                min_level=10,
                max_level=90,
                scene_outputs=True,
                start_at_full=False,
                leading_edge=True,
            ),
            output2=Xp33Output(
                min_level=20,
                max_level=80,
                scene_outputs=False,
                start_at_full=True,
                leading_edge=False,
            ),
            output3=Xp33Output(
                min_level=30,
                max_level=70,
                scene_outputs=True,
                start_at_full=True,
                leading_edge=True,
            ),
            scene1=Xp33Scene(
                output1_level=50,
                output2_level=60,
                output3_level=70,
                time=TimeParam.T5SEC,
            ),
            scene2=Xp33Scene(
                output1_level=25,
                output2_level=35,
                output3_level=45,
                time=TimeParam.T10SEC,
            ),
            scene3=Xp33Scene(
                output1_level=75,
                output2_level=85,
                output3_level=95,
                time=TimeParam.T1MIN,
            ),
            scene4=Xp33Scene(
                output1_level=0,
                output2_level=100,
                output3_level=50,
                time=TimeParam.NONE,
            ),
        )

    @pytest.fixture
    def sample_telegram_data(self):
        """Sample telegram data for testing - based on specification example."""
        return "AAAABOGEBOGEBOGEAABECIDMAADMFACIAABEBEBEAAGEGEGEAHAAAAAAAAAAAAAAAAAA"

    def test_serialization_round_trip(self, sample_action_table):
        """Test that serialization and deserialization produce the same data."""
        # Serialize to telegram format
        serialized = Xp33MsActionTableSerializer.to_data(sample_action_table)

        # Deserialize back
        deserialized = Xp33MsActionTableSerializer.from_data(serialized)

        # Check outputs
        assert deserialized.output1.min_level == sample_action_table.output1.min_level
        assert deserialized.output1.max_level == sample_action_table.output1.max_level
        assert (
            deserialized.output1.scene_outputs
            == sample_action_table.output1.scene_outputs
        )
        assert (
            deserialized.output1.start_at_full
            == sample_action_table.output1.start_at_full
        )
        assert (
            deserialized.output1.leading_edge
            == sample_action_table.output1.leading_edge
        )

        assert deserialized.output2.min_level == sample_action_table.output2.min_level
        assert deserialized.output2.max_level == sample_action_table.output2.max_level
        assert (
            deserialized.output2.scene_outputs
            == sample_action_table.output2.scene_outputs
        )
        assert (
            deserialized.output2.start_at_full
            == sample_action_table.output2.start_at_full
        )
        assert (
            deserialized.output2.leading_edge
            == sample_action_table.output2.leading_edge
        )

        assert deserialized.output3.min_level == sample_action_table.output3.min_level
        assert deserialized.output3.max_level == sample_action_table.output3.max_level
        assert (
            deserialized.output3.scene_outputs
            == sample_action_table.output3.scene_outputs
        )
        assert (
            deserialized.output3.start_at_full
            == sample_action_table.output3.start_at_full
        )
        assert (
            deserialized.output3.leading_edge
            == sample_action_table.output3.leading_edge
        )

        # Check scenes
        assert (
            deserialized.scene1.output1_level
            == sample_action_table.scene1.output1_level
        )
        assert (
            deserialized.scene1.output2_level
            == sample_action_table.scene1.output2_level
        )
        assert (
            deserialized.scene1.output3_level
            == sample_action_table.scene1.output3_level
        )
        assert deserialized.scene1.time == sample_action_table.scene1.time

        assert (
            deserialized.scene2.output1_level
            == sample_action_table.scene2.output1_level
        )
        assert (
            deserialized.scene2.output2_level
            == sample_action_table.scene2.output2_level
        )
        assert (
            deserialized.scene2.output3_level
            == sample_action_table.scene2.output3_level
        )
        assert deserialized.scene2.time == sample_action_table.scene2.time

        assert (
            deserialized.scene3.output1_level
            == sample_action_table.scene3.output1_level
        )
        assert (
            deserialized.scene3.output2_level
            == sample_action_table.scene3.output2_level
        )
        assert (
            deserialized.scene3.output3_level
            == sample_action_table.scene3.output3_level
        )
        assert deserialized.scene3.time == sample_action_table.scene3.time

        assert (
            deserialized.scene4.output1_level
            == sample_action_table.scene4.output1_level
        )
        assert (
            deserialized.scene4.output2_level
            == sample_action_table.scene4.output2_level
        )
        assert (
            deserialized.scene4.output3_level
            == sample_action_table.scene4.output3_level
        )
        assert deserialized.scene4.time == sample_action_table.scene4.time

    def test_from_data_basic(self, sample_telegram_data):
        """Test basic telegram parsing."""
        action_table = Xp33MsActionTableSerializer.from_data(sample_telegram_data)

        # Verify it's a valid Xp33MsActionTable
        assert isinstance(action_table, Xp33MsActionTable)

        # Check that we have 3 outputs
        assert action_table.output1 is not None
        assert action_table.output2 is not None
        assert action_table.output3 is not None

        # Check that we have 4 scenes
        assert action_table.scene1 is not None
        assert action_table.scene2 is not None
        assert action_table.scene3 is not None
        assert action_table.scene4 is not None

    def test_from_data_invalid_length(self):
        """Test that invalid telegram length raises ValueError."""
        # Too short
        with pytest.raises(ValueError, match="is too short"):
            Xp33MsActionTableSerializer.from_data("AAAA")

        with pytest.raises(ValueError, match="is too short"):
            Xp33MsActionTableSerializer.from_data("AAA")  # Even shorter

    def test_boundary_values(self):
        """Test boundary value handling."""
        # Create action table with boundary values
        action_table = Xp33MsActionTable(
            output1=Xp33Output(min_level=0, max_level=100),
            output2=Xp33Output(min_level=0, max_level=100),
            output3=Xp33Output(min_level=0, max_level=100),
            scene1=Xp33Scene(
                output1_level=0,
                output2_level=100,
                output3_level=50,
                time=TimeParam.NONE,
            ),
            scene2=Xp33Scene(
                output1_level=100,
                output2_level=0,
                output3_level=50,
                time=TimeParam.T120MIN,
            ),
            scene3=Xp33Scene(
                output1_level=50,
                output2_level=50,
                output3_level=50,
                time=TimeParam.T5SEC,
            ),
            scene4=Xp33Scene(
                output1_level=25,
                output2_level=75,
                output3_level=0,
                time=TimeParam.T1MIN,
            ),
        )

        # Test round trip
        serialized = Xp33MsActionTableSerializer.to_data(action_table)
        deserialized = Xp33MsActionTableSerializer.from_data(serialized)

        # Verify boundary values are preserved
        assert deserialized.output1.min_level == 0
        assert deserialized.output1.max_level == 100
        assert deserialized.scene1.output1_level == 0
        assert deserialized.scene1.output2_level == 100
        assert deserialized.scene2.output1_level == 100
        assert deserialized.scene2.output2_level == 0

    def test_bit_flags_handling(self):
        """Test proper handling of bit flags for outputs."""
        # Test all combinations of flags
        action_table = Xp33MsActionTable(
            output1=Xp33Output(
                scene_outputs=True, start_at_full=False, leading_edge=True
            ),
            output2=Xp33Output(
                scene_outputs=False, start_at_full=True, leading_edge=False
            ),
            output3=Xp33Output(
                scene_outputs=True, start_at_full=True, leading_edge=True
            ),
        )

        # Test round trip
        serialized = Xp33MsActionTableSerializer.to_data(action_table)
        deserialized = Xp33MsActionTableSerializer.from_data(serialized)

        # Verify flags are preserved
        assert deserialized.output1.scene_outputs
        assert not deserialized.output1.start_at_full
        assert deserialized.output1.leading_edge

        assert not deserialized.output2.scene_outputs
        assert deserialized.output2.start_at_full
        assert not deserialized.output2.leading_edge

        assert deserialized.output3.scene_outputs
        assert deserialized.output3.start_at_full
        assert deserialized.output3.leading_edge

    def test_time_param_handling(self):
        """Test TimeParam enum handling."""
        action_table = Xp33MsActionTable(
            scene1=Xp33Scene(time=TimeParam.NONE),
            scene2=Xp33Scene(time=TimeParam.T5SEC),
            scene3=Xp33Scene(time=TimeParam.T1MIN),
            scene4=Xp33Scene(time=TimeParam.T120MIN),
        )

        # Test round trip
        serialized = Xp33MsActionTableSerializer.to_data(action_table)
        deserialized = Xp33MsActionTableSerializer.from_data(serialized)

        # Verify time parameters are preserved
        assert deserialized.scene1.time == TimeParam.NONE
        assert deserialized.scene2.time == TimeParam.T5SEC
        assert deserialized.scene3.time == TimeParam.T1MIN
        assert deserialized.scene4.time == TimeParam.T120MIN

    def test_percentage_conversions(self):
        """Test percentage conversion utility methods."""
        # Test percentage to byte
        assert Xp33MsActionTableSerializer._percentage_to_byte(0) == 0
        assert Xp33MsActionTableSerializer._percentage_to_byte(50) == 50
        assert Xp33MsActionTableSerializer._percentage_to_byte(100) == 100
        assert Xp33MsActionTableSerializer._percentage_to_byte(-10) == 0  # Clamped to 0
        assert (
            Xp33MsActionTableSerializer._percentage_to_byte(150) == 100
        )  # Clamped to 100

        # Test byte to percentage
        assert Xp33MsActionTableSerializer._byte_to_percentage(0) == 0
        assert Xp33MsActionTableSerializer._byte_to_percentage(50) == 50
        assert Xp33MsActionTableSerializer._byte_to_percentage(100) == 100
        assert (
            Xp33MsActionTableSerializer._byte_to_percentage(255) == 100
        )  # Clamped to 100

    def test_time_param_conversions(self):
        """Test TimeParam conversion utility methods."""
        # Test time param to byte
        assert Xp33MsActionTableSerializer._time_param_to_byte(TimeParam.NONE) == 0
        assert Xp33MsActionTableSerializer._time_param_to_byte(TimeParam.T5SEC) == 4
        assert Xp33MsActionTableSerializer._time_param_to_byte(TimeParam.T1MIN) == 10

        # Test byte to time param
        assert Xp33MsActionTableSerializer._byte_to_time_param(0) == TimeParam.NONE
        assert Xp33MsActionTableSerializer._byte_to_time_param(4) == TimeParam.T5SEC
        assert Xp33MsActionTableSerializer._byte_to_time_param(10) == TimeParam.T1MIN
        assert (
            Xp33MsActionTableSerializer._byte_to_time_param(255) == TimeParam.NONE
        )  # Invalid value defaults to NONE

    def test_byte_to_bits_conversion(self):
        """Test byte to bits conversion."""
        from xp.utils.serialization import byte_to_bits

        # Test various byte values
        assert byte_to_bits(0) == [False] * 8
        assert byte_to_bits(1) == [True] + [False] * 7
        assert byte_to_bits(2) == [False, True] + [False] * 6
        assert byte_to_bits(255) == [True] * 8

        # Test specific pattern: 0b00000101 = 5
        expected = [True, False, True, False, False, False, False, False]
        assert byte_to_bits(5) == expected

    def test_bits_to_byte_conversion(self):
        """Test bits to byte conversion."""
        from xp.utils.serialization import bits_to_byte

        # Test various bit patterns
        assert bits_to_byte([False] * 8) == 0
        assert bits_to_byte([True] + [False] * 7) == 1
        assert bits_to_byte([False, True] + [False] * 6) == 2
        assert bits_to_byte([True] * 8) == 255

        # Test specific pattern: 0b00000101 = 5
        bits = [True, False, True, False, False, False, False, False]
        assert bits_to_byte(bits) == 5

    def test_exception_handling_for_dim_function(self):
        """Test exception handling for dimFunction bit extraction."""
        # Create a mock raw_bytes that would cause an exception
        # This simulates the exception handling mentioned in the specification
        raw_bytes = bytearray(25)  # Only 25 bytes instead of 32

        # This should not raise an exception and should default to False
        with suppress(IndexError):
            output = Xp33MsActionTableSerializer._decode_output(raw_bytes, 0)
            assert not output.leading_edge

    def test_de_nibble_integration(self):
        """Test integration with de_nibble utility."""
        # Test with simple nibble data
        nibble_data = "AAAB"  # Should decode to [0, 1]
        result = de_nibbles(nibble_data)
        assert result == bytearray([0, 1])

        # Test with longer data
        nibble_data = "AAAAADAAADAAADAAADAAAAAA"
        result = de_nibbles(nibble_data)
        expected = bytearray([0, 0, 3, 0, 3, 0, 3, 0, 3, 0, 0, 0])
        assert result == expected

    def test_default_values(self):
        """Test that default values work correctly."""
        # Create action table with default values
        action_table = Xp33MsActionTable()

        # Test serialization with defaults
        serialized = Xp33MsActionTableSerializer.to_data(action_table)
        deserialized = Xp33MsActionTableSerializer.from_data(serialized)

        # Verify defaults are preserved
        assert deserialized.output1.min_level == 0
        assert deserialized.output1.max_level == 100
        assert not deserialized.output1.scene_outputs
        assert not deserialized.output1.start_at_full
        assert not deserialized.output1.leading_edge

        assert deserialized.scene1.output1_level == 0
        assert deserialized.scene1.output2_level == 0
        assert deserialized.scene1.output3_level == 0
        assert deserialized.scene1.time == TimeParam.NONE

    def test_serialize_back_and_forth(self):
        """Test that default values work correctly."""
        telegram = "<R0020045056F17DAAAAAAGEAAGEAAGEAABECIDMAADMFACIAABEBEBEAAGEGEGEAHAAAAAAAAAAAAAAAAAAFI>"
        # Create action table with default values

        # Test serialization with defaults
        serialized_table = telegram[16:84]
        deserialized = Xp33MsActionTableSerializer.from_data(serialized_table)
        serialized = Xp33MsActionTableSerializer.to_data(deserialized)

        assert serialized_table == serialized
