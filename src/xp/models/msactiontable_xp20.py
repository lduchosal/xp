"""XP20 Action Table models for input actions and settings."""

from dataclasses import dataclass, field


@dataclass
class InputChannel:
    invert: bool = False
    short_long: bool = False
    group_on_off: bool = False
    and_functions: list[bool] = field(default_factory=list)
    sa_function: bool = False
    ta_function: bool = False


@dataclass
class Xp20MsActionTable:
    """
    XP320 Action Table for managing input
    """

    input1: InputChannel = field(default_factory=InputChannel)
    input2: InputChannel = field(default_factory=InputChannel)
    input3: InputChannel = field(default_factory=InputChannel)
    input4: InputChannel = field(default_factory=InputChannel)
    input5: InputChannel = field(default_factory=InputChannel)
    input6: InputChannel = field(default_factory=InputChannel)
    input7: InputChannel = field(default_factory=InputChannel)
    input8: InputChannel = field(default_factory=InputChannel)

