"""XP33 Action Table models for output and scene configuration."""

from dataclasses import dataclass, field

from xp.models.timeparam_type import TimeParam


@dataclass
class Xp33Output:
    """Represents an XP33 output configuration"""

    min_level: int = 0
    max_level: int = 100
    scene_outputs: bool = False
    start_at_full: bool = False
    leading_edge: bool = False


@dataclass
class Xp33Scene:
    """Represents a scene configuration"""

    output1_level: int = 0
    output2_level: int = 0
    output3_level: int = 0
    time: TimeParam = TimeParam.NONE


@dataclass
class Xp33MsActionTable:
    """
    XP33 Action Table for managing outputs and scenes
    """

    output1: Xp33Output = field(default_factory=Xp33Output)
    output2: Xp33Output = field(default_factory=Xp33Output)
    output3: Xp33Output = field(default_factory=Xp33Output)

    scene1: Xp33Scene = field(default_factory=Xp33Scene)
    scene2: Xp33Scene = field(default_factory=Xp33Scene)
    scene3: Xp33Scene = field(default_factory=Xp33Scene)
    scene4: Xp33Scene = field(default_factory=Xp33Scene)
