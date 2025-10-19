"""XP20 Action Table models for input actions and settings."""

from dataclasses import dataclass, field


@dataclass
class InputChannel:
    """Configuration for a single input channel in XP20 action table.

    Attributes:
        invert: Input inversion flag
        short_long: Short/long press detection flag
        group_on_off: Group on/off function flag
        and_functions: 8-bit AND function configuration array
        sa_function: SA function flag
        ta_function: TA function flag
    """

    invert: bool = False
    short_long: bool = False
    group_on_off: bool = False
    and_functions: list[bool] = field(default_factory=lambda: [False] * 8)
    sa_function: bool = False
    ta_function: bool = False


@dataclass
class Xp20MsActionTable:
    """XP20 Action Table for managing 8 input channels.

    Contains configuration for 8 input channels (input1 through input8),
    each with flags for inversion, short/long press detection, group functions,
    AND functions, SA functions, and TA functions.

    Attributes:
        input1: Configuration for input channel 1.
        input2: Configuration for input channel 2.
        input3: Configuration for input channel 3.
        input4: Configuration for input channel 4.
        input5: Configuration for input channel 5.
        input6: Configuration for input channel 6.
        input7: Configuration for input channel 7.
        input8: Configuration for input channel 8.
    """

    input1: InputChannel = field(default_factory=InputChannel)
    input2: InputChannel = field(default_factory=InputChannel)
    input3: InputChannel = field(default_factory=InputChannel)
    input4: InputChannel = field(default_factory=InputChannel)
    input5: InputChannel = field(default_factory=InputChannel)
    input6: InputChannel = field(default_factory=InputChannel)
    input7: InputChannel = field(default_factory=InputChannel)
    input8: InputChannel = field(default_factory=InputChannel)
