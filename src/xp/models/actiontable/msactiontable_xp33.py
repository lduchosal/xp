"""XP33 Action Table models for output and scene configuration."""

from dataclasses import dataclass, field

from xp.models.telegram.timeparam_type import TimeParam


@dataclass
class Xp33Output:
    """Represents an XP33 output configuration.

    Attributes:
        min_level: Minimum output level (0-100).
        max_level: Maximum output level (0-100).
        scene_outputs: Enable scene outputs.
        start_at_full: Start at full brightness.
        leading_edge: Use leading edge dimming.
    """

    min_level: int = 0
    max_level: int = 100
    scene_outputs: bool = False
    start_at_full: bool = False
    leading_edge: bool = False


@dataclass
class Xp33Scene:
    """Represents a scene configuration.

    Attributes:
        output1_level: Output level for output 1 (0-100).
        output2_level: Output level for output 2 (0-100).
        output3_level: Output level for output 3 (0-100).
        time: Time parameter for scene transition.
    """

    output1_level: int = 0
    output2_level: int = 0
    output3_level: int = 0
    time: TimeParam = TimeParam.NONE


@dataclass
class Xp33MsActionTable:
    """XP33 Action Table for managing outputs and scenes.

    Attributes:
        output1: Configuration for output 1.
        output2: Configuration for output 2.
        output3: Configuration for output 3.
        scene1: Configuration for scene 1.
        scene2: Configuration for scene 2.
        scene3: Configuration for scene 3.
        scene4: Configuration for scene 4.
    """

    output1: Xp33Output = field(default_factory=Xp33Output)
    output2: Xp33Output = field(default_factory=Xp33Output)
    output3: Xp33Output = field(default_factory=Xp33Output)

    scene1: Xp33Scene = field(default_factory=Xp33Scene)
    scene2: Xp33Scene = field(default_factory=Xp33Scene)
    scene3: Xp33Scene = field(default_factory=Xp33Scene)
    scene4: Xp33Scene = field(default_factory=Xp33Scene)
