# Copyright (c) 2025 ldvchosal
"""XP33 Action Table models for output and scene configuration."""

from pydantic import BaseModel, Field, field_validator

from xp.models.telegram.timeparam_type import TimeParam

# Maximum output/scene level in percent
MAX_LEVEL = 100

# Prefixed lines split into exactly two parts: "<prefix><num>" and parameters
LINE_PART_COUNT = 2


class Xp33Output(BaseModel):
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


class Xp33Scene(BaseModel):
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

    @field_validator("time", mode="before")
    @classmethod
    def validate_time_param(cls, v: object) -> TimeParam:
        """Convert string or int to TimeParam enum.

        Args:
            v: Input value (can be string name, int value, or enum).

        Returns:
            TimeParam enum value.

        Raises:
            ValueError: If the value cannot be converted to TimeParam.

        """
        if isinstance(v, TimeParam):
            return v
        if isinstance(v, str):
            try:
                return TimeParam[v]
            except KeyError as e:
                msg = f"Invalid TimeParam: {v}"
                raise ValueError(msg) from e
        if isinstance(v, int):
            try:
                return TimeParam(v)
            except ValueError as e:
                msg = f"Invalid TimeParam value: {v}"
                raise ValueError(msg) from e
        msg = f"Invalid type for TimeParam: {type(v)}"
        raise ValueError(msg)


class Xp33MsActionTable(BaseModel):
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

    output1: Xp33Output = Field(default_factory=Xp33Output)
    output2: Xp33Output = Field(default_factory=Xp33Output)
    output3: Xp33Output = Field(default_factory=Xp33Output)

    scene1: Xp33Scene = Field(default_factory=Xp33Scene)
    scene2: Xp33Scene = Field(default_factory=Xp33Scene)
    scene3: Xp33Scene = Field(default_factory=Xp33Scene)
    scene4: Xp33Scene = Field(default_factory=Xp33Scene)

    def to_short_format(self) -> list[str]:
        """Convert action table to short format string.

        Returns:
            Short format string (multi-line format with OUT and SCENE lines).

        """
        lines = []

        # Format outputs
        outputs = [
            (1, self.output1),
            (2, self.output2),
            (3, self.output3),
        ]
        for num, output in outputs:
            lines.append(f"OUT{num} {self._format_output(output)}")

        # Format scenes
        scenes = [
            (1, self.scene1),
            (2, self.scene2),
            (3, self.scene3),
            (4, self.scene4),
        ]
        for num, scene in scenes:
            lines.append(f"SCENE{num} {self._format_scene(scene)}")

        return lines

    @classmethod
    def from_short_format(cls, short_str: list[str]) -> "Xp33MsActionTable":
        """Parse short format string into action table.

        Args:
            short_str: Short format string (list of lines).

        Returns:
            Xp33MsActionTable instance.

        Raises:
            ValueError: If format is invalid.

        """
        # Parse outputs and scenes from lines
        outputs: dict[int, Xp33Output] = {}
        scenes: dict[int, Xp33Scene] = {}

        for raw_line in short_str:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("OUT"):
                out_num, output = cls._parse_output_line(line)
                outputs[out_num] = output
            elif line.startswith("SCENE"):
                scene_num, scene = cls._parse_scene_line(line)
                scenes[scene_num] = scene

        # Validate we have all required outputs and scenes
        for i in (1, 2, 3):
            if i not in outputs:
                msg = f"Missing output{i} configuration"
                raise ValueError(msg)

        for i in (1, 2, 3, 4):
            if i not in scenes:
                msg = f"Missing scene{i} configuration"
                raise ValueError(msg)

        return cls(
            output1=outputs[1],
            output2=outputs[2],
            output3=outputs[3],
            scene1=scenes[1],
            scene2=scenes[2],
            scene3=scenes[3],
            scene4=scenes[4],
        )

    @classmethod
    def _parse_output_line(cls, line: str) -> tuple[int, Xp33Output]:
        """Parse an output line like "OUT1 MIN:0 MAX:100 SO:0 SF:0 LE:0".

        Args:
            line: Stripped output line starting with "OUT".

        Returns:
            Tuple of (output number, parsed Xp33Output).

        Raises:
            ValueError: If the line format is invalid.

        """
        parts = line.split(None, 1)
        if len(parts) != LINE_PART_COUNT:
            msg = f"Invalid output line format: '{line}'"
            raise ValueError(msg)

        out_key = parts[0]  # OUT1, OUT2, OUT3
        try:
            out_num = int(out_key[3:])
        except ValueError as e:
            msg = f"Invalid output number in: '{out_key}'"
            raise ValueError(msg) from e
        if out_num not in {1, 2, 3}:
            msg = f"Invalid output number in: '{out_key}'"
            raise ValueError(msg)

        return out_num, cls._parse_output(parts[1])

    @classmethod
    def _parse_scene_line(cls, line: str) -> tuple[int, Xp33Scene]:
        """Parse a scene line like "SCENE1 OUT1:0 OUT2:0 OUT3:0 T:NONE".

        Args:
            line: Stripped scene line starting with "SCENE".

        Returns:
            Tuple of (scene number, parsed Xp33Scene).

        Raises:
            ValueError: If the line format is invalid.

        """
        parts = line.split(None, 1)
        if len(parts) != LINE_PART_COUNT:
            msg = f"Invalid scene line format: '{line}'"
            raise ValueError(msg)

        scene_key = parts[0]  # SCENE1, SCENE2, etc.
        try:
            scene_num = int(scene_key[5:])
        except ValueError as e:
            msg = f"Invalid scene number in: '{scene_key}'"
            raise ValueError(msg) from e
        if scene_num not in {1, 2, 3, 4}:
            msg = f"Invalid scene number in: '{scene_key}'"
            raise ValueError(msg)

        return scene_num, cls._parse_scene(parts[1])

    @staticmethod
    def _format_output(output: Xp33Output) -> str:
        """Format output configuration to short string.

        Args:
            output: Xp33Output instance.

        Returns:
            Short string like "MIN:10 MAX:90 SO:1 SF:0 LE:1".

        """
        return (
            f"MIN:{output.min_level} "
            f"MAX:{output.max_level} "
            f"SO:{1 if output.scene_outputs else 0} "
            f"SF:{1 if output.start_at_full else 0} "
            f"LE:{1 if output.leading_edge else 0}"
        )

    @staticmethod
    def _parse_output(output_str: str) -> Xp33Output:
        """Parse output configuration from short string.

        Args:
            output_str: Short string like "MIN:10 MAX:90 SO:1 SF:0 LE:1".

        Returns:
            Xp33Output instance.

        Raises:
            ValueError: If format is invalid.

        """
        # Parse key:value pairs
        parts = output_str.split()
        params = {}

        for part in parts:
            if ":" not in part:
                msg = f"Invalid output parameter format: '{part}'"
                raise ValueError(msg)

            key, value = part.split(":", 1)
            params[key] = value

        # Validate required keys
        required_keys = ["MIN", "MAX", "SO", "SF", "LE"]
        for key in required_keys:
            if key not in params:
                msg = f"Missing required parameter: {key}"
                raise ValueError(msg)

        # Parse and validate values
        try:
            min_level = int(params["MIN"])
            max_level = int(params["MAX"])
            scene_outputs = params["SO"] == "1"
            start_at_full = params["SF"] == "1"
            leading_edge = params["LE"] == "1"

            # Validate ranges
            Xp33MsActionTable._validate_level(min_level, "MIN")
            Xp33MsActionTable._validate_level(max_level, "MAX")

            return Xp33Output(
                min_level=min_level,
                max_level=max_level,
                scene_outputs=scene_outputs,
                start_at_full=start_at_full,
                leading_edge=leading_edge,
            )
        except ValueError as e:
            msg = f"Invalid output parameter value: {e}"
            raise ValueError(msg) from e

    @staticmethod
    def _validate_level(level: int, label: str) -> None:
        """Validate that a level value is within the 0-100 range.

        Args:
            level: Level value to validate.
            label: Parameter label used in the error message.

        Raises:
            ValueError: If the level is out of range.

        """
        if not (0 <= level <= MAX_LEVEL):
            msg = f"{label} level out of range (0-100): {level}"
            raise ValueError(msg)

    @staticmethod
    def _format_scene(scene: Xp33Scene) -> str:
        """Format scene configuration to short string.

        Args:
            scene: Xp33Scene instance.

        Returns:
            Short string like "OUT1:50 OUT2:60 OUT3:70 T:T5SEC".

        """
        time_str = scene.time.name
        return (
            f"OUT1:{scene.output1_level} "
            f"OUT2:{scene.output2_level} "
            f"OUT3:{scene.output3_level} "
            f"T:{time_str}"
        )

    @staticmethod
    def _parse_scene(scene_str: str) -> Xp33Scene:
        """Parse scene configuration from short string.

        Args:
            scene_str: Short string like "OUT1:50 OUT2:60 OUT3:70 T:T5SEC".

        Returns:
            Xp33Scene instance.

        Raises:
            ValueError: If format is invalid.

        """
        # Parse key:value pairs
        parts = scene_str.split()
        params = {}

        for part in parts:
            if ":" not in part:
                msg = f"Invalid scene parameter format: '{part}'"
                raise ValueError(msg)

            key, value = part.split(":", 1)
            params[key] = value

        # Validate required keys
        required_keys = ["OUT1", "OUT2", "OUT3", "T"]
        for key in required_keys:
            if key not in params:
                msg = f"Missing required parameter: {key}"
                raise ValueError(msg)

        # Parse and validate values
        try:
            output1_level = int(params["OUT1"])
            output2_level = int(params["OUT2"])
            output3_level = int(params["OUT3"])

            # Validate ranges
            Xp33MsActionTable._validate_level(output1_level, "OUT1")
            Xp33MsActionTable._validate_level(output2_level, "OUT2")
            Xp33MsActionTable._validate_level(output3_level, "OUT3")

            # Parse time parameter - support both name and numeric value
            time_param = Xp33MsActionTable._parse_time_param(params["T"])

            return Xp33Scene(
                output1_level=output1_level,
                output2_level=output2_level,
                output3_level=output3_level,
                time=time_param,
            )
        except ValueError as e:
            msg = f"Invalid scene parameter value: {e}"
            raise ValueError(msg) from e

    @staticmethod
    def _parse_time_param(time_str: str) -> TimeParam:
        """Parse a time parameter given as enum name or numeric value.

        Args:
            time_str: Time parameter string (e.g., "T5SEC" or "12").

        Returns:
            TimeParam enum value.

        Raises:
            ValueError: If the value cannot be converted to TimeParam.

        """
        try:
            # Try parsing as enum name first
            time_param = TimeParam[time_str]
        except KeyError:
            # Try parsing as numeric value
            try:
                time_value = int(time_str)
                time_param = TimeParam(time_value)
            except (ValueError, KeyError) as e:
                msg = f"Invalid TimeParam: '{time_str}'"
                raise ValueError(msg) from e
        return time_param
