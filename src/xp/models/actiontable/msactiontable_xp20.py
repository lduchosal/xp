"""XP20 Action Table models for input actions and settings."""

from pydantic import BaseModel, Field


class InputChannel(BaseModel):
    """
    Configuration for a single input channel in XP20 action table.

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
    and_functions: list[bool] = Field(default_factory=lambda: [False] * 8)
    sa_function: bool = False
    ta_function: bool = False


class Xp20MsActionTable(BaseModel):
    """
    XP20 Action Table for managing 8 input channels.

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

    input1: InputChannel = Field(default_factory=InputChannel)
    input2: InputChannel = Field(default_factory=InputChannel)
    input3: InputChannel = Field(default_factory=InputChannel)
    input4: InputChannel = Field(default_factory=InputChannel)
    input5: InputChannel = Field(default_factory=InputChannel)
    input6: InputChannel = Field(default_factory=InputChannel)
    input7: InputChannel = Field(default_factory=InputChannel)
    input8: InputChannel = Field(default_factory=InputChannel)

    def to_short_format(self) -> list[str]:
        """
        Convert action table to short format string.

        Returns:
            Short format string with each channel on a separate line.
            Example:
                CH1 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
                CH2 I:0 S:0 G:0 AND:00000000 SA:0 TA:0
                ...
        """
        lines = []
        for i in range(1, 9):
            channel = getattr(self, f"input{i}")
            # Convert and_functions list to binary string
            and_bits = "".join("1" if bit else "0" for bit in channel.and_functions)
            line = (
                f"CH{i} "
                f"I:{1 if channel.invert else 0} "
                f"S:{1 if channel.short_long else 0} "
                f"G:{1 if channel.group_on_off else 0} "
                f"AND:{and_bits} "
                f"SA:{1 if channel.sa_function else 0} "
                f"TA:{1 if channel.ta_function else 0}"
            )
            lines.append(line)
        return lines

    @classmethod
    def from_short_format(cls, short_str: list[str]) -> "Xp20MsActionTable":
        """
        Parse short format string into action table.

        Args:
            short_str: Short format string with 8 channel lines.

        Returns:
            Xp20MsActionTable instance.

        Raises:
            ValueError: If format is invalid.
        """
        import re

        if len(short_str) != 8:
            raise ValueError(f"Expected 8 channel lines, got {len(short_str)}")

        pattern = re.compile(
            r"^CH([1-8]) I:([01]) S:([01]) G:([01]) AND:([01]{8}) SA:([01]) TA:([01])$"
        )

        channels = {}
        for line in short_str:
            line = line.strip()
            match = pattern.match(line)
            if not match:
                raise ValueError(f"Invalid channel format: {line}")

            ch_num = int(match.group(1))
            invert = match.group(2) == "1"
            short_long = match.group(3) == "1"
            group_on_off = match.group(4) == "1"
            and_bits = match.group(5)
            sa_function = match.group(6) == "1"
            ta_function = match.group(7) == "1"

            # Convert binary string to list of bools
            and_functions = [bit == "1" for bit in and_bits]

            channels[ch_num] = InputChannel(
                invert=invert,
                short_long=short_long,
                group_on_off=group_on_off,
                and_functions=and_functions,
                sa_function=sa_function,
                ta_function=ta_function,
            )

        # Verify all channels are present
        for i in range(1, 9):
            if i not in channels:
                raise ValueError(f"Missing channel {i}")

        return cls(
            input1=channels[1],
            input2=channels[2],
            input3=channels[3],
            input4=channels[4],
            input5=channels[5],
            input6=channels[6],
            input7=channels[7],
            input8=channels[8],
        )
