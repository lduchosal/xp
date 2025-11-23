"""Unit tests for XP33 Action Table Short Format."""

import pytest

from xp.models.actiontable.msactiontable_xp33 import (
    Xp33MsActionTable,
    Xp33Output,
    Xp33Scene,
)
from xp.models.telegram.timeparam_type import TimeParam


class TestXp33ShortFormat:
    """Test cases for XP33 short format conversion."""

    @pytest.fixture
    def default_action_table(self):
        """Create default action table for testing."""
        return Xp33MsActionTable()

    @pytest.fixture
    def sample_action_table(self):
        """Create sample action table with non-default values."""
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

    def test_to_short_format_default(self, default_action_table):
        """Test conversion to short format with default values."""
        short = default_action_table.to_short_format()

        expected = [
            "OUT1 MIN:0 MAX:100 SO:0 SF:0 LE:0",
            "OUT2 MIN:0 MAX:100 SO:0 SF:0 LE:0",
            "OUT3 MIN:0 MAX:100 SO:0 SF:0 LE:0",
            "SCENE1 OUT1:0 OUT2:0 OUT3:0 T:NONE",
            "SCENE2 OUT1:0 OUT2:0 OUT3:0 T:NONE",
            "SCENE3 OUT1:0 OUT2:0 OUT3:0 T:NONE",
            "SCENE4 OUT1:0 OUT2:0 OUT3:0 T:NONE",
        ]

        assert short == expected

    def test_to_short_format_sample(self, sample_action_table):
        """Test conversion to short format with sample values."""
        short = sample_action_table.to_short_format()

        expected = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        assert short == expected

    def test_from_short_format_default(self):
        """Test parsing short format with default values."""
        short_str = [
            "OUT1 MIN:0 MAX:100 SO:0 SF:0 LE:0",
            "OUT2 MIN:0 MAX:100 SO:0 SF:0 LE:0",
            "OUT3 MIN:0 MAX:100 SO:0 SF:0 LE:0",
            "SCENE1 OUT1:0 OUT2:0 OUT3:0 T:NONE",
            "SCENE2 OUT1:0 OUT2:0 OUT3:0 T:NONE",
            "SCENE3 OUT1:0 OUT2:0 OUT3:0 T:NONE",
            "SCENE4 OUT1:0 OUT2:0 OUT3:0 T:NONE",
        ]

        action_table = Xp33MsActionTable.from_short_format(short_str)

        # Validate outputs
        assert action_table.output1.min_level == 0
        assert action_table.output1.max_level == 100
        assert action_table.output1.scene_outputs is False
        assert action_table.output1.start_at_full is False
        assert action_table.output1.leading_edge is False

        # Validate scenes
        assert action_table.scene1.output1_level == 0
        assert action_table.scene1.output2_level == 0
        assert action_table.scene1.output3_level == 0
        assert action_table.scene1.time == TimeParam.NONE

    def test_from_short_format_sample(self):
        """Test parsing short format with sample values."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        action_table = Xp33MsActionTable.from_short_format(short_str)

        # Validate output1
        assert action_table.output1.min_level == 10
        assert action_table.output1.max_level == 90
        assert action_table.output1.scene_outputs is True
        assert action_table.output1.start_at_full is False
        assert action_table.output1.leading_edge is True

        # Validate output2
        assert action_table.output2.min_level == 20
        assert action_table.output2.max_level == 80
        assert action_table.output2.scene_outputs is False
        assert action_table.output2.start_at_full is True
        assert action_table.output2.leading_edge is False

        # Validate output3
        assert action_table.output3.min_level == 30
        assert action_table.output3.max_level == 70
        assert action_table.output3.scene_outputs is True
        assert action_table.output3.start_at_full is True
        assert action_table.output3.leading_edge is True

        # Validate scene1
        assert action_table.scene1.output1_level == 50
        assert action_table.scene1.output2_level == 60
        assert action_table.scene1.output3_level == 70
        assert action_table.scene1.time == TimeParam.T5SEC

        # Validate scene4
        assert action_table.scene4.output1_level == 0
        assert action_table.scene4.output2_level == 100
        assert action_table.scene4.output3_level == 50
        assert action_table.scene4.time == TimeParam.NONE

    def test_round_trip_conversion(self, sample_action_table):
        """Test that to_short_format and from_short_format are inverses."""
        # Convert to short format
        short = sample_action_table.to_short_format()

        # Parse back
        parsed = Xp33MsActionTable.from_short_format(short)

        # Should equal the original
        assert parsed.output1.min_level == sample_action_table.output1.min_level
        assert parsed.output1.max_level == sample_action_table.output1.max_level
        assert parsed.output1.scene_outputs == sample_action_table.output1.scene_outputs
        assert parsed.output1.start_at_full == sample_action_table.output1.start_at_full
        assert parsed.output1.leading_edge == sample_action_table.output1.leading_edge

        assert parsed.scene1.output1_level == sample_action_table.scene1.output1_level
        assert parsed.scene1.output2_level == sample_action_table.scene1.output2_level
        assert parsed.scene1.output3_level == sample_action_table.scene1.output3_level
        assert parsed.scene1.time == sample_action_table.scene1.time

    def test_boundary_values(self):
        """Test boundary value handling."""
        action_table = Xp33MsActionTable(
            output1=Xp33Output(min_level=0, max_level=100),
            output2=Xp33Output(min_level=0, max_level=100),
            output3=Xp33Output(min_level=0, max_level=100),
            scene1=Xp33Scene(output1_level=0, output2_level=100, output3_level=50),
            scene2=Xp33Scene(output1_level=100, output2_level=0, output3_level=50),
            scene3=Xp33Scene(output1_level=50, output2_level=50, output3_level=50),
            scene4=Xp33Scene(output1_level=25, output2_level=75, output3_level=0),
        )

        # Convert and parse back
        parsed = Xp33MsActionTable.from_short_format(action_table.to_short_format())

        # Verify boundary values
        assert parsed.output1.min_level == 0
        assert parsed.output1.max_level == 100
        assert parsed.scene1.output1_level == 0
        assert parsed.scene1.output2_level == 100
        assert parsed.scene2.output1_level == 100
        assert parsed.scene2.output2_level == 0

    def test_all_time_params(self):
        """Test all TimeParam enum values."""
        for time_param in TimeParam:
            scene = Xp33Scene(
                output1_level=50, output2_level=60, output3_level=70, time=time_param
            )

            action_table = Xp33MsActionTable(scene1=scene)

            # Convert and parse back
            short = action_table.to_short_format()
            parsed = Xp33MsActionTable.from_short_format(short)

            # Verify time parameter is preserved
            assert parsed.scene1.time == time_param

    def test_all_flag_combinations(self):
        """Test all combinations of output flags."""
        flag_combinations = [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (False, False, True),
            (True, True, False),
            (True, False, True),
            (False, True, True),
            (True, True, True),
        ]

        for so, sf, le in flag_combinations:
            output = Xp33Output(scene_outputs=so, start_at_full=sf, leading_edge=le)

            action_table = Xp33MsActionTable(output1=output)

            # Convert and parse back
            short = action_table.to_short_format()
            parsed = Xp33MsActionTable.from_short_format(short)

            # Verify flags are preserved
            assert parsed.output1.scene_outputs == so
            assert parsed.output1.start_at_full == sf
            assert parsed.output1.leading_edge == le

    def test_invalid_format_missing_output(self):
        """Test error handling for missing output."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1",
            # Missing OUT2
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="Missing output2"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_format_missing_scene(self):
        """Test error handling for missing scene."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC",
            # Missing SCENE3
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="Missing scene3"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_output_number(self):
        """Test error handling for invalid output number."""
        short_str = [
            "OUT5 MIN:10 MAX:90 SO:1 SF:0 LE:1\n",  # Invalid OUT5
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC\n",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="Invalid output number"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_scene_number(self):
        """Test error handling for invalid scene number."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1\n",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC\n",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE9 OUT1:0 OUT2:100 OUT3:50 T:NONE",  # Invalid SCENE9
        ]

        with pytest.raises(ValueError, match="Invalid scene number"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_output_parameter_missing(self):
        """Test error handling for missing output parameter."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 LE:1\n",  # Missing SF
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC\n",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="Missing required parameter"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_scene_parameter_missing(self):
        """Test error handling for missing scene parameter."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1\n",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 T:T5SEC\n",  # Missing OUT3
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="Missing required parameter"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_output_level_range(self):
        """Test error handling for out-of-range output levels."""
        short_str = [
            "OUT1 MIN:10 MAX:150 SO:1 SF:0 LE:1\n",  # MAX > 100
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC\n",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="out of range"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_scene_level_range(self):
        """Test error handling for out-of-range scene levels."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1\n",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:150 OUT2:60 OUT3:70 T:T5SEC\n",  # OUT1 > 100
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="out of range"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_invalid_time_param(self):
        """Test error handling for invalid TimeParam."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1\n",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:INVALID\n",  # Invalid time param
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE",
        ]

        with pytest.raises(ValueError, match="Invalid TimeParam"):
            Xp33MsActionTable.from_short_format(short_str)

    def test_numeric_time_param(self):
        """Test parsing numeric TimeParam values."""
        short_str = [
            "OUT1 MIN:10 MAX:90 SO:1 SF:0 LE:1\n",
            "OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0\n",
            "OUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:4\n",  # Numeric value for T5SEC
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:5\n",  # Numeric value for T10SEC
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:10\n",  # Numeric value for T1MIN
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:0\n",  # Numeric value for NONE
        ]

        action_table = Xp33MsActionTable.from_short_format(short_str)

        # Verify time parameters
        assert action_table.scene1.time == TimeParam.T5SEC
        assert action_table.scene2.time == TimeParam.T10SEC
        assert action_table.scene3.time == TimeParam.T1MIN
        assert action_table.scene4.time == TimeParam.NONE

    def test_whitespace_handling(self):
        """Test that extra whitespace is handled correctly."""
        short_str = [
            "OUT1  MIN:10  MAX:90  SO:1  SF:0  LE:1\n",
            "  OUT2 MIN:20 MAX:80 SO:0 SF:1 LE:0  \n",
            "\nOUT3 MIN:30 MAX:70 SO:1 SF:1 LE:1\n",
            "SCENE1 OUT1:50 OUT2:60 OUT3:70 T:T5SEC\n",
            "SCENE2 OUT1:25 OUT2:35 OUT3:45 T:T10SEC\n",
            "SCENE3 OUT1:75 OUT2:85 OUT3:95 T:T1MIN\n",
            "SCENE4 OUT1:0 OUT2:100 OUT3:50 T:NONE\n",
        ]

        # Should parse successfully despite extra whitespace
        action_table = Xp33MsActionTable.from_short_format(short_str)

        assert action_table.output1.min_level == 10
        assert action_table.output2.min_level == 20
        assert action_table.output3.min_level == 30
